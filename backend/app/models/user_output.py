"""用户输出管理模块，负责论文结果的拼接、引用处理和保存。"""

import os
import re
from app.utils.data_recorder import DataRecorder
from app.schemas.A2A import WriterResponse
import json
import uuid


class UserOutput:
    """管理建模任务的输出结果，处理引用编号、脚注和最终论文拼接。"""
    def __init__(
        self, work_dir: str, ques_count: int, data_recorder: DataRecorder | None = None
    ):
        self.work_dir = work_dir
        self.res: dict[str, dict] = {}
        self.data_recorder = data_recorder
        self.cost_time = 0.0
        self.initialized = True
        self.ques_count: int = ques_count
        self.footnotes: dict[str, dict] = {}
        self._init_seq()

    def _init_seq(self):
        ques_str = [f"ques{i}" for i in range(1, self.ques_count + 1)]
        self.seq = [
            "firstPage",
            "RepeatQues",
            "analysisQues",
            "modelAssumption",
            "symbol",
            "eda",
            *ques_str,
            "sensitivity_analysis",
            "judge",
        ]

    def set_res(self, key: str, writer_response: WriterResponse):
        """设置指定章节的写作结果。

        Accumulates footnotes from each section into self.footnotes.
        Footnotes from WriterResponse are (num_str, content) tuples with new-style
        `[^num]` markers already in the text.
        """
        text = writer_response.response_content or ""

        # Handle footnotes from WriterResponse (new style)
        if writer_response.footnotes:
            footnotes_list = writer_response.footnotes
            for num_str, content in footnotes_list:
                # Assign a UUID key for dedup
                existing_uuid = None
                for uid, fdata in self.footnotes.items():
                    if fdata["content"] == content:
                        existing_uuid = uid
                        break
                if existing_uuid is None:
                    uid_key = str(uuid.uuid4())
                    self.footnotes[uid_key] = {"content": content}
                # Note: markers like [^1] stay in text, we manage them at save time
        else:
            # Legacy fallback: extract {[^N]: citation} from text
            text = self._legacy_extract_footnotes(text)

        self.res[key] = {
            "response_content": text,
            "footnotes": writer_response.footnotes,
        }

    def _legacy_extract_footnotes(self, text: str) -> str:
        """Extract {[^N]: citation} inline citations from legacy format."""
        pattern = r"\{\[\^(\d+)\]:\s*(.*?)\}"
        matches = re.findall(pattern, text, re.DOTALL)
        for ref_num, ref_content in matches:
            ref_content = ref_content.strip().rstrip(".")
            existing_uuid = None
            for uid, fdata in self.footnotes.items():
                if fdata["content"] == ref_content:
                    existing_uuid = uid
                    break
            if existing_uuid:
                text = re.sub(
                    rf"\{{\[\^{ref_num}\]:.*?\}}",
                    f"[{existing_uuid}]",
                    text,
                    flags=re.DOTALL,
                )
            else:
                new_uuid = str(uuid.uuid4())
                self.footnotes[new_uuid] = {"content": ref_content}
                text = re.sub(
                    rf"\{{\[\^{ref_num}\]:.*?\}}",
                    f"[{new_uuid}]",
                    text,
                    flags=re.DOTALL,
                )
        return text

    def get_res(self):
        """获取所有章节的写作结果。"""
        return self.res

    def get_model_build_solve(self) -> str:
        """获取模型求解结果的摘要字符串。"""
        model_build_solve = ",".join(
            f"{key}-{value}"
            for key, value in self.res.items()
            if key.startswith("ques") and key != "ques_count"
        )
        return model_build_solve

    def _collect_all_references(self) -> dict[str, tuple[str, int]]:
        """Collect all references across sections and assign sequential numbers.

        Returns {uuid_key: (content, seq_number)}.
        """
        # First pass: collect all [^num] markers and map them to content
        num_to_uuid: dict[int, str] = {}
        for key in self.seq:
            if key not in self.res:
                continue
            text = self.res[key]["response_content"]
            # Match both UUID-style and numeric-style markers
            uuid_markers = re.findall(r"\[([a-f0-9-]{36})\]|\[\^(\d+)\]", text)
            for uuid_match, num_match in uuid_markers:
                if uuid_match:
                    if uuid_match not in self.footnotes:
                        continue
                    content = self.footnotes[uuid_match]["content"]
                    # Assign sequence number
                    num = int(self.footnotes[uuid_match].get("number", 0))
                    if num == 0:
                        # Hasn't been numbered yet; defer to second pass
                        pass
                elif num_match:
                    num = int(num_match)
                    # Check if this marker maps to a known footnote content
                    # by looking for the content in existing footnotes
                    # (Handled in second pass)

        # Second pass: assign sequential numbers
        all_refs: dict[str, tuple[str, int]] = {}
        seq_num = 1

        for key in self.seq:
            if key not in self.res:
                continue
            text = self.res[key]["response_content"]
            # Find everything that looks like a marker
            uuid_markers = re.findall(r"\[([a-f0-9-]{36})\]|\[\^(\d+)\]", text)
            for uuid_match, num_match in uuid_markers:
                if uuid_match and uuid_match in self.footnotes:
                    content = self.footnotes[uuid_match]["content"]
                    if uuid_match not in all_refs:
                        all_refs[uuid_match] = (content, seq_num)
                        self.footnotes[uuid_match]["number"] = seq_num
                        seq_num += 1
                elif num_match and not uuid_match:
                    # Handle inline [^num] from writer — check if already stored
                    num = int(num_match)
                    # Find content by number in footnotes or inline text
                    inline_pattern = rf"\[\^{num}\]:\s*(.*?)(?=\n\[\^|$)"
                    inline_match = re.search(inline_pattern, text, re.DOTALL)
                    if inline_match:
                        content = inline_match.group(1).strip().rstrip(".")
                        uid_key = f"inline_{num}"
                        if uid_key not in all_refs:
                            all_refs[uid_key] = (content, seq_num)
                            self.footnotes[uid_key] = {"content": content, "number": seq_num}
                            seq_num += 1

        return all_refs

    def get_result_to_save(self) -> str:
        """获取最终拼接的论文全文，包含引用处理和参考文献。

        For new-style citations: text already has [^N] markers and footnotes
        are tracked in self.footnotes. We dedup, renumber, and append the
        reference list.
        """
        # Collect and renumber all references
        all_refs = self._collect_all_references()

        # Build ordered reference text
        sorted_refs = sorted(all_refs.items(), key=lambda x: x[1][1])  # sort by seq number

        # Join all sections in order
        sections_text = ""
        for key in self.seq:
            if key not in self.res:
                continue
            text = self.res[key]["response_content"]

            # Renumber UUID markers: [uuid] → [^N]
            def _replace_uuid(m: re.Match) -> str:
                uid = m.group(1)
                if uid in all_refs:
                    return f"[^{all_refs[uid][1]}]"
                return m.group(0)

            text = re.sub(r"\[([a-f0-9-]{36})\]", _replace_uuid, text)
            sections_text += "\n\n" + text if sections_text else text

        # Append reference section
        if sorted_refs:
            sections_text += "\n\n## References"
            for uid, (content, num) in sorted_refs:
                sections_text += f"\n\n[^{num}]: {content}"

        return sections_text

    def save_result(self):
        """将结果保存为 res.json 和 res.md 文件。"""
        with open(os.path.join(self.work_dir, "res.json"), "w", encoding="utf-8") as f:
            json.dump(self.res, f, ensure_ascii=False, indent=4)

        res_path = os.path.join(self.work_dir, "res.md")
        with open(res_path, "w", encoding="utf-8") as f:
            f.write(self.get_result_to_save())
