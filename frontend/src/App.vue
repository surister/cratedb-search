<template>
  <v-app>
    <v-main>
      <div>
        raw:
        <CrateSearchBase/>
      </div>

      <div>
        not raw:
        <CrateSearchBase>
          <template #content="results">
               {{ results }}
          </template>
        </CrateSearchBase>
      </div>
    </v-main>
  </v-app>
</template>

<script setup>
import CrateSearchBase from "@/components/CrateSearchBase.vue";
</script>
