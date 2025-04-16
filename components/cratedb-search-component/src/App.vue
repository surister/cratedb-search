<template>
  <v-app>
    <v-main>
      <div>
        raw:
        <CrateSearchBase/>
      </div>
      <br><br>
      <div>
        not raw:
        <CrateSearchBase v-model="otherobj">
          <template #content="results">
               {{ results }}
          </template>
        </CrateSearchBase>
      </div>
    </v-main>
  </v-app>
</template>

<script setup>
import CrateSearchBase from "@/components/SearchBase.vue";
let otherobj = [
  {name: 1}, {name: 3}
]
</script>
