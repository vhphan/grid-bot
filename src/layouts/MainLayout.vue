<template>
  <q-layout view="hHh lpR fFf">

    <q-header elevated class="bg-primary text-white" height-hint="98">
      <q-toolbar>
        <q-btn dense flat round icon="menu" @click="toggleLeftDrawer"/>

        <q-toolbar-title>
          <q-avatar>
            <q-icon name="insights"/>
          </q-avatar>
          Grid Bot Project: {{ symbol }}
        </q-toolbar-title>

        <q-tabs align="left">
          <!--          <q-route-tab to="/page1" label="Page One"/>-->
          <!--          <q-route-tab to="/page2" label="Page Two"/>-->
          <!--          <q-route-tab to="/page3" label="Page Three"/>-->
        </q-tabs>
        <q-btn dense flat round icon="menu" @click="toggleRightDrawer"/>
      </q-toolbar>

    </q-header>

    <q-drawer v-model="leftDrawerOpen" side="left" bordered>
      drawer
    </q-drawer>

    <!--    <q-drawer-->
    <!--        v-model="rightDrawerOpen"-->
    <!--        side="right"-->
    <!--        bordered-->
    <!--        :width="500"-->
    <!--    >-->
    <!--      right drawer-->
    <!--    </q-drawer>-->

    <q-page-container>
      <home/>
    </q-page-container>

  </q-layout>
</template>

<script>
import {ref} from 'vue'
import Home from "../components/Home.vue";

export default {
  name: "MainLayout",
  components: {Home},
  setup() {
    const leftDrawerOpen = ref(false)
    const rightDrawerOpen = ref(true)
    const symbol = import.meta.env.VITE_SYMBOL;
    return {
      symbol,
      leftDrawerOpen,
      toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value
      },
      rightDrawerOpen,
      toggleRightDrawer() {
        rightDrawerOpen.value = !rightDrawerOpen.value
      },
    }
  }
}
</script>

<style scoped>

</style>