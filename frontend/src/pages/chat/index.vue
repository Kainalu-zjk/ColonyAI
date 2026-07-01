<script setup lang="ts">
import { getHelloWorld } from "@/apis/commonApi";
import AppSidebar from "@/components/AppSidebar.vue";
import ServiceStatus from "@/components/ServiceStatus.vue";
import UserStepper from "@/components/UserStepper.vue";
import Button from "@/components/ui/button/Button.vue";
import {
	SidebarInset,
	SidebarProvider,
	SidebarTrigger,
} from "@/components/ui/sidebar";
import MoreDetail from "@/pages/chat/components/MoreDetail.vue";
import { CircleEllipsis } from "lucide-vue-next";
import { onMounted, ref } from "vue";
// ---- Reactive State ----

const isMoreDetailOpen = ref(false);

// ---- Lifecycle Hooks ----

onMounted(() => {
	getHelloWorld().then((res) => {
		console.log(res.data);
	});
});
</script>

<template>

  <SidebarProvider>
    <MoreDetail v-model="isMoreDetailOpen" />
    <AppSidebar />
    <SidebarInset>
      <header class="flex h-16 shrink-0 items-center gap-2 px-4">
        <SidebarTrigger class="-ml-1" />
        <div class="flex justify-between w-full gap-2">
          <ServiceStatus />
          <div class="flex gap-2">
            <Button variant="outline" @click="isMoreDetailOpen = true">
              <CircleEllipsis />
              更多
            </Button>
          </div>
        </div>
      </header>

      <div class="py-5 px-4">
        <div class="space-y-6">
          <div class="text-center space-y-2 mb-10">
            <h1 class="text-2xl font-semibold">
              <span class="gradient-text">Colony AI</span>
            </h1>
            <p class="text-muted-foreground">
              智衍 · 让 Agent 协作完成建模、代码编写、论文写作
            </p>
          </div>

          <UserStepper>
          </UserStepper>
          <div class="text-center text-xs text-muted-foreground mt-8">
            项目处于内测阶段，欢迎进群反馈
          </div>
        </div>
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>

<style scoped>
.gradient-text {
  background: linear-gradient(to right, #2DD4BF, #6366F1);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
</style>
