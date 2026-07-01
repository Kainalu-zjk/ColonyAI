import { defineStore } from "pinia";
import { ref } from "vue";

/** 任务历史记录项 */
export interface TaskHistoryItem {
	taskId: string;
	title: string;
	template: string;
	status: "running" | "completed" | "failed";
	createdAt: string;
}

/** 任务历史记录 Store（持久化到 localStorage） */
export const useTaskHistoryStore = defineStore("taskHistory", () => {
	const STORAGE_KEY = "colony_ai_task_history";

	/** 历史任务列表（最新的在前面） */
	const tasks = ref<TaskHistoryItem[]>(_load());

	function _load(): TaskHistoryItem[] {
		try {
			const raw = localStorage.getItem(STORAGE_KEY);
			if (raw) {
				const parsed = JSON.parse(raw);
				if (Array.isArray(parsed)) {
					return parsed;
				}
			}
		} catch {
			// ignore
		}
		return [];
	}

	function _save() {
		try {
			localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks.value));
		} catch {
			// ignore
		}
	}

	/** 添加一条任务记录 */
	function add(item: TaskHistoryItem) {
		// 去重：如果已存在相同 taskId，先移除旧的
		tasks.value = tasks.value.filter((t) => t.taskId !== item.taskId);
		tasks.value.unshift(item);
		// 限制最多 50 条
		if (tasks.value.length > 50) {
			tasks.value = tasks.value.slice(0, 50);
		}
		_save();
	}

	/** 更新任务状态 */
	function updateStatus(taskId: string, status: TaskHistoryItem["status"]) {
		const item = tasks.value.find((t) => t.taskId === taskId);
		if (item) {
			item.status = status;
			_save();
		}
	}

	/** 更新任务标题 */
	function updateTitle(taskId: string, title: string) {
		const item = tasks.value.find((t) => t.taskId === taskId);
		if (item) {
			item.title = title;
			_save();
		}
	}

	/** 删除一条记录 */
	function remove(taskId: string) {
		tasks.value = tasks.value.filter((t) => t.taskId !== taskId);
		_save();
	}

	/** 清空所有记录 */
	function clear() {
		tasks.value = [];
		_save();
	}

	return {
		tasks,
		add,
		updateStatus,
		updateTitle,
		remove,
		clear,
	};
});
