import request from "@/utils/request";

/** 中文模板名 → 后端枚举值的映射 */
function _mapTemplate(template?: string): string {
	const map: Record<string, string> = {
		"国赛": "CHINA",
		"美赛": "AMERICAN",
		"华数杯": "HUASHU",
		"华为杯": "HUAWEI",
	};
	return map[template ?? ""] || "CHINA";
}

/**
 * 提交数学建模任务
 * @param problem 问题描述
 * @param files 上传的数据文件
 */
export function submitModelingTask(
	problem: {
		ques_all: string;
		comp_template?: string;
		format_output?: string;
		lang?: string;
	},
	files?: File[],
) {
	const formData = new FormData();
	// 添加问题数据
	formData.append("ques_all", problem.ques_all);
	formData.append("comp_template", _mapTemplate(problem.comp_template));
	formData.append("format_output", problem.format_output || "Markdown");
	formData.append("lang", problem.lang || "zh");

	if (files) {
		// file 是文件对象

		// 添加文件
		if (files) {
			for (const file of files) {
				formData.append("files", file);
			}
		}

		return request.post<{
			task_id: string;
			status: string;
		}>("/modeling", formData, {
			headers: {
				"Content-Type": "multipart/form-data",
			},
			timeout: 30000, // 添加超时设置
		});
	}
}
