<template>
  <q-layout view="lHh lpR lFf">

    <q-header elevated class="bg-primary text-white" height-hint="98">
      <q-toolbar>
        <q-btn dense flat round icon="menu" @click="toggleLeftDrawer"/>

        <q-toolbar-title>
          <q-avatar>
            <q-icon name="insights"/>
          </q-avatar>
          Title
        </q-toolbar-title>

        <q-tabs align="left">
<!--          <q-route-tab to="/page1" label="Page One"/>-->
<!--          <q-route-tab to="/page2" label="Page Two"/>-->
<!--          <q-route-tab to="/page3" label="Page Three"/>-->
        </q-tabs>
      </q-toolbar>

    </q-header>

    <q-drawer v-model="leftDrawerOpen" side="left" bordered>
      <!-- drawer content -->
      drawer
    </q-drawer>

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

    return {
      leftDrawerOpen,
      toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value
      }
    }
  }
}
</script>

<style scoped>

</style>