<script setup lang="ts">
import { useRouter } from "vue-router";
import { useTaskHistoryStore, type TaskHistoryItem } from "@/stores/taskHistory";
import { History, X, Clock, CheckCircle, AlertCircle } from "lucide-vue-next";
import { ref } from "vue";

const taskHistoryStore = useTaskHistoryStore();
const router = useRouter();
const isOpen = ref(false);

function statusIcon(status: TaskHistoryItem["status"]) {
	switch (status) {
		case "running":
			return Clock;
		case "completed":
			return CheckCircle;
		case "failed":
			return AlertCircle;
	}
}

function statusClass(status: TaskHistoryItem["status"]) {
	switch (status) {
		case "running":
			return "text-blue-500";
		case "completed":
			return "text-green-500";
		case "failed":
			return "text-red-500";
	}
}

function formatDate(iso: string) {
	try {
		const d = new Date(iso);
		return d.toLocaleString("zh-CN", {
			month: "2-digit",
			day: "2-digit",
			hour: "2-digit",
			minute: "2-digit",
		});
	} catch {
		return iso;
	}
}

function goToTask(taskId: string) {
	router.push(`/task/${taskId}`);
}

function removeTask(e: Event, taskId: string) {
	e.stopPropagation();
	taskHistoryStore.remove(taskId);
}
</script>

<template>
  <SidebarGroup>
    <SidebarGroupLabel class="flex items-center justify-between cursor-pointer" @click="isOpen = !isOpen">
      <div class="flex items-center gap-2">
        <History class="w-3.5 h-3.5" />
        <span>历史任务</span>
      </div>
      <span class="text-xs text-muted-foreground">{{ taskHistoryStore.tasks.length }}</span>
    </SidebarGroupLabel>

    <SidebarGroupContent v-if="isOpen && taskHistoryStore.tasks.length > 0">
      <SidebarMenu>
        <SidebarMenuItem v-for="task in taskHistoryStore.tasks.slice(0, 20)" :key="task.taskId">
          <div
            class="flex items-start gap-2 px-2 py-1.5 rounded-md hover:bg-sidebar-accent cursor-pointer text-sm group"
            @click="goToTask(task.taskId)"
          >
            <component :is="statusIcon(task.status)" :class="statusClass(task.status)" class="w-3.5 h-3.5 mt-0.5 shrink-0" />
            <div class="flex-1 min-w-0">
              <p class="truncate text-xs font-medium">{{ task.title }}</p>
              <div class="flex items-center gap-2 text-[10px] text-muted-foreground">
                <span>{{ task.template }}</span>
                <span>{{ formatDate(task.createdAt) }}</span>
              </div>
            </div>
            <button
              class="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
              @click="removeTask($event, task.taskId)"
            >
              <X class="w-3 h-3" />
            </button>
          </div>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarGroupContent>

    <SidebarGroupContent v-else-if="isOpen">
      <p class="px-2 text-xs text-muted-foreground">暂无历史任务</p>
    </SidebarGroupContent>
  </SidebarGroup>
</template>
