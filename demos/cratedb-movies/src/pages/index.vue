<script lang="ts" setup>
import {SearchBase, hybrid_search} from 'cratedb-search-component';
import {ref} from "vue";

const results = ref([])
const search_term = ref("")
const drawer = ref(false)
const loading = ref(false)
const info_item = ref(null)
</script>

<template>
  <v-navigation-drawer
    v-model="drawer"
    :location="$vuetify.display.mobile ? 'bottom' : undefined"
    temporary
  >
   <v-container v-if="info_item">
     <span class="text-h6">Rank:</span> {{ info_item[0] }}<br>
     <span class="text-h6">Id:</span> {{ info_item[1] }}<br>
     <span class="text-h6">Movie name:</span> {{ info_item[6] }}<br>
     <span class="text-h6">Release date</span> {{ info_item[7]['release_date'] }}<br>
     <span class="text-h6">Description</span> {{ info_item[4] }}<br>
     <span class="text-h6">Movie name:</span> {{ info_item[6] }}<br>
     <v-img
       :src="`https://image.tmdb.org/t/p/w300_and_h450_bestv2/${info_item[5]}.jpg`"
       class="align-end"
       gradient="to bottom, rgba(0,0,0,.1), rgba(0,0,0,.5)"
       height="200px"
       cover>
     </v-img>
   </v-container>
  </v-navigation-drawer>

  <v-container>
    <v-card class="d-flex align-center text-grey-darken-4 justify-center"
            variant="outlined"
            style="background: rgba(209,168,108,0.37)"
    >
      <v-card-text>
        <v-row justify="center">
          <v-col
            align-self="center"
            cols="auto">
            <span>
              <span class="text-h2 font-weight-bold">Movie search by </span>
              <a href="https://cratedb.com"
                 target="_blank">
                <v-img
                  inline
                  width="300"
                  src="@/assets/cratedb.svg"/>
              </a>
            </span>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    <SearchBase v-model="results">
      <template #input>
        <v-text-field label="Search"
                      variant="outlined"
                      class="text-grey-darken-4 mt-5"
                      v-model="search_term"
                      @click:clear="results = []"
                      clearable
                      hide-details>
          <template v-slot:loader>
            <v-progress-linear
              v-if="loading"
              class="mt-1"
              color="red"
              model-value="100"
              height="7"
              indeterminate
            ></v-progress-linear>
          </template>
        </v-text-field>
      </template>
      <template #button>
        <v-btn variant="outlined"
               class="text-grey-darken-4 my-5"
               :loading="loading"
               @click="()=>{
                 loading = true
                 hybrid_search(search_term).then((query_results) => {
                 query_results.json().then((r) => {
                   results = r['result']
                   loading = false
                 })
               })}">Search
        </v-btn>
      </template>
      <template #content="{results}">
        <v-row dense>
          <v-col v-for="result in results" cols="2">
            <template v-if="results">
              <v-card class="transform-me" @click="console.log(1)">
                <v-img
                  :src="`https://image.tmdb.org/t/p/w300_and_h450_bestv2/${result[5]}.jpg`"
                  class="align-end"
                  gradient="to bottom, rgba(0,0,0,.1), rgba(0,0,0,.5)"
                  height="200px"
                  @click="()=>{
                    info_item = result
                    drawer = true
                  }"
                  cover>
                </v-img>
                <v-card-text class="pb-0 px-2 pt-1">
                  {{ result[3] }}
                </v-card-text>
                <v-card-subtitle class="pb-1 pl-2">
                  <span class="text-subtitle-2">{{ result[7]['release_date'] }}</span>
                </v-card-subtitle>

              </v-card>
            </template>
            <template v-else>
              <v-img></v-img>
            </template>
          </v-col>
        </v-row>
      </template>
    </SearchBase>


  </v-container>
</template>

<style>
main {
  background-color: #ee5522;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 2000 1500'%3E%3Cdefs%3E%3CradialGradient id='a' gradientUnits='objectBoundingBox'%3E%3Cstop offset='0' stop-color='%23FB3'/%3E%3Cstop offset='1' stop-color='%23ee5522'/%3E%3C/radialGradient%3E%3ClinearGradient id='b' gradientUnits='userSpaceOnUse' x1='0' y1='750' x2='1550' y2='750'%3E%3Cstop offset='0' stop-color='%23f7882b'/%3E%3Cstop offset='1' stop-color='%23ee5522'/%3E%3C/linearGradient%3E%3Cpath id='s' fill='url(%23b)' d='M1549.2 51.6c-5.4 99.1-20.2 197.6-44.2 293.6c-24.1 96-57.4 189.4-99.3 278.6c-41.9 89.2-92.4 174.1-150.3 253.3c-58 79.2-123.4 152.6-195.1 219c-71.7 66.4-149.6 125.8-232.2 177.2c-82.7 51.4-170.1 94.7-260.7 129.1c-90.6 34.4-184.4 60-279.5 76.3C192.6 1495 96.1 1502 0 1500c96.1-2.1 191.8-13.3 285.4-33.6c93.6-20.2 185-49.5 272.5-87.2c87.6-37.7 171.3-83.8 249.6-137.3c78.4-53.5 151.5-114.5 217.9-181.7c66.5-67.2 126.4-140.7 178.6-218.9c52.3-78.3 96.9-161.4 133-247.9c36.1-86.5 63.8-176.2 82.6-267.6c18.8-91.4 28.6-184.4 29.6-277.4c0.3-27.6 23.2-48.7 50.8-48.4s49.5 21.8 49.2 49.5c0 0.7 0 1.3-0.1 2L1549.2 51.6z'/%3E%3Cg id='g'%3E%3Cuse href='%23s' transform='scale(0.12) rotate(60)'/%3E%3Cuse href='%23s' transform='scale(0.2) rotate(10)'/%3E%3Cuse href='%23s' transform='scale(0.25) rotate(40)'/%3E%3Cuse href='%23s' transform='scale(0.3) rotate(-20)'/%3E%3Cuse href='%23s' transform='scale(0.4) rotate(-30)'/%3E%3Cuse href='%23s' transform='scale(0.5) rotate(20)'/%3E%3Cuse href='%23s' transform='scale(0.6) rotate(60)'/%3E%3Cuse href='%23s' transform='scale(0.7) rotate(10)'/%3E%3Cuse href='%23s' transform='scale(0.835) rotate(-40)'/%3E%3Cuse href='%23s' transform='scale(0.9) rotate(40)'/%3E%3Cuse href='%23s' transform='scale(1.05) rotate(25)'/%3E%3Cuse href='%23s' transform='scale(1.2) rotate(8)'/%3E%3Cuse href='%23s' transform='scale(1.333) rotate(-60)'/%3E%3Cuse href='%23s' transform='scale(1.45) rotate(-30)'/%3E%3Cuse href='%23s' transform='scale(1.6) rotate(10)'/%3E%3C/g%3E%3C/defs%3E%3Cg transform='rotate(0 0 0)'%3E%3Cg transform='rotate(0 0 0)'%3E%3Ccircle fill='url(%23a)' r='3000'/%3E%3Cg opacity='0.5'%3E%3Ccircle fill='url(%23a)' r='2000'/%3E%3Ccircle fill='url(%23a)' r='1800'/%3E%3Ccircle fill='url(%23a)' r='1700'/%3E%3Ccircle fill='url(%23a)' r='1651'/%3E%3Ccircle fill='url(%23a)' r='1450'/%3E%3Ccircle fill='url(%23a)' r='1250'/%3E%3Ccircle fill='url(%23a)' r='1175'/%3E%3Ccircle fill='url(%23a)' r='900'/%3E%3Ccircle fill='url(%23a)' r='750'/%3E%3Ccircle fill='url(%23a)' r='500'/%3E%3Ccircle fill='url(%23a)' r='380'/%3E%3Ccircle fill='url(%23a)' r='250'/%3E%3C/g%3E%3Cg transform='rotate(0 0 0)'%3E%3Cuse href='%23g' transform='rotate(10)'/%3E%3Cuse href='%23g' transform='rotate(120)'/%3E%3Cuse href='%23g' transform='rotate(240)'/%3E%3C/g%3E%3Ccircle fill-opacity='0.1' fill='url(%23a)' r='3000'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  background-attachment: fixed;
  background-size: cover;
}
.transform-me:hover {
  transform: scale(1.2);
  z-index: 1000;
  transition: all .3s ease;
}
* {
  font-family: Roboto, serif;
}

</style>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,100;0,300;0,400;0,700;0,900;1,100;1,300;1,400;1,700;1,900&family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&family=Rubik:ital,wght@0,300..900;1,300..900&display=swap" rel="stylesheet">
