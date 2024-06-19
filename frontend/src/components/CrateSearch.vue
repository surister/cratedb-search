<script setup>
import {ref, watch} from "vue";

import OpenAI from "openai";


const search2 = ref('')
const data = ref()
const crate_uri = 'http://192.168.88.251:4200'
const knn_search_options = ref({
  results: 10, // How many results will the knn return
  schema: 'doc',
  table: 'fs_vec_big2',
  vector_column_name: 'xs',
  openai_token: import.meta.env.VITE_OPENAI_TOKEN,
  model_dimensions: 2048,
  model: 'text-embedding-3-large',
  text: 'scalar knn search',
  join_table_name: 'fs_search5',
  join_table_on: '_id',
  vec_join_table_on: 'fs_search_id',
  selects_from_join: '1'
})

const fs_search_options = ref({
  schema: 'doc',
  table: ['fs_search5'],
  multiple: false,
  column: 'content, title',
  text: 'scalar knn search',
  selected_fields: '*',
  results: []
})

const hybrid_search_options = ref({
  text: '',
  results: []
})
const openai = new OpenAI({
  apiKey: knn_search_options.value.openai_token,
  dangerouslyAllowBrowser: true
});

async function request_crate(_stmt, query_params = '', sql_stmt_params = {}, is_from_console = false) {

  let url = crate_uri + '/_sql' + '?types'
  let stmt = _stmt // https://airbnb.io/javascript/#functions--reassign-params

  if (query_params) {
    url = url + '&' + query_params
  }

  if (stmt.endsWith(';')) {
    // We remove it.
    stmt = stmt.slice(0, -1)
  }

  if (sql_stmt_params) {
    Object.entries(sql_stmt_params).map(entry => {
      stmt = stmt.replace(entry[0], entry[1] != null ? entry[1] : '')
    });
  }


  try {
    const request = await fetch(
      url,
      {
        method: 'POST',
        cache: 'no-cache',
        body: JSON.stringify({'stmt': stmt}),
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    return request

  } catch (err) {

  }
}

async function request_hybrid_search(fs_table, fs_columns, fs_search_term, fs_fuzziness, vector_table, vector_column, vector, vector_limit) {

  const query = `WITH fs as (SELECT _score                             AS fs_score,
                                    _id                                as fs_id,
                                    RANK() over (ORDER BY _score DESC) as fs_rank
                             FROM %fs_table
                             WHERE MATCH ((%fs_columns), '%fs_search_term') USING best_fields
                             with (fuzziness = %fs_fuzziness)
                             ORDER BY fs_score DESC
                             LIMIT 10),
                      vec as (SELECT _score,
                                     fs_search_id,
                                     RANK() over (ORDER BY _score DESC) as vec_rank
                              FROM %vector_table
                              WHERE KNN_MATCH("%vector_column", [%vector], %vector_limit)
                              ORDER BY _score DESC
                              LIMIT 10),
                      hybrid as (SELECT fs.fs_id                AS id_from_fs,
                                        vec.fs_search_id        AS id_from_vec,
                                        vec.vec_rank,
                                        fs.fs_rank
                                 FROM fs FULL JOIN vec
                                 ON fs.fs_id = vec.fs_search_id)
                 SELECT fs.title, hybrid.vec_rank, hybrid.fs_rank, fs.content_html, fs.section_hierarchy, fs.metadata['url']
                 FROM hybrid,
                      fs_search5 fs
                 WHERE fs._id = hybrid.id_from_fs
                    OR fs._id = hybrid.id_from_vec`

  const _response = await request_crate(query, null,
    {
      '%fs_table': fs_table,
      '%fs_columns': fs_columns,
      '%fs_search_term': fs_search_term,
      '%fs_fuzziness': fs_fuzziness,
      '%vector_table': vector_table,
      '%vector_column': vector_column,
      '%vector': vector,
      '%vector_limit': vector_limit
    })
  const data = await _response.json()
  return data
}

async function hybrid_search() {
  const embedding = await openai.embeddings.create({
    model: knn_search_options.value.model,
    input: hybrid_search_options.value.text,
    dimensions: parseInt(knn_search_options.value.model_dimensions)
  });
  const vector = embedding.data[0].embedding

  const result = await request_hybrid_search(
    fs_search_options.value.table,
    fs_search_options.value.column,
    hybrid_search_options.value.text,
    1,
    knn_search_options.value.table,
    knn_search_options.value.vector_column_name,
    vector,
    10
  )
    hybrid_search_options.value.results = {
      headers: result.cols,
      rows: result.rows
    }
  for (const resultElement of result.rows) {
    let vec_rank = resultElement[1] || 0;
    let fs_rank = resultElement[2] || 0;
    let final_rank = 0;

    // If fulltext search rank exists, we boost it
    // a little bit, to make mit more prevalent than
    // vector search, this is the equivalent of
    // having weight = 0.1 in the RRF calculation
    // below.
    if (fs_rank !== 0) {
      fs_rank -= .1
    }

    for (const fsRankElement of [vec_rank, fs_rank]) {
      if (fsRankElement !== 0) {
        final_rank += 1 / (fsRankElement + 0)
      }
    }

    resultElement.push(
      final_rank
    )
  }
  let sorted = result.rows.sort((a, b) => {
    return b[a.length - 1] - a[a.length - 1]
  })
  result.cols.push('final_weight')
  hybrid_search_options.value.results = {
    headers: result.cols,
    rows: sorted
  }
}

function debounce(func, timeout = 100) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      func.apply(this, args);
    }, timeout);
  };
}


const search = debounce(() => hybrid_search());

watch(() => search2.value, async () => {
  const request = await request_crate(`
    SELECT _score,
           *
    FROM fs_search4
    WHERE MATCH(content, '${search2.value}')
    ORDER BY _score DESC
    LIMIT 10
  `)
  data.value = await request.json()
})
watch(() => hybrid_search_options.value.text, () => {
  console.log('Debouncing')
  search()
})

const highlight = function (text, search_term) {
  const regex = new RegExp(search_term, "gi")
  return text.replaceAll(regex, `<span style="color: red">${search_term}</span>`)
}

const compact_results = ref(true)
const compact_results_0 = ref(true)
</script>

<template>

  <v-container><h1><v-icon>mdi-alert</v-icon>INTERNAL PREVIEW FOR CRATE.IO ONLY</h1></v-container>
<v-container>
  <v-row class="mt-5">
    <v-col>
      <v-label>Only with fulltext search</v-label>
      <v-card variant="outlined">
        <v-card-title>
          <v-row>
            <v-col>Search CrateDB docs</v-col>
            <v-spacer></v-spacer>
            <v-col class="text-right">
              <v-btn size="small"
                     class="ml-2"
                     text="Compact results"
                     variant="tonal"
                     :prepend-icon="compact_results ? 'mdi-check-circle-outline': 'mdi-circle-outline'"
                     @click="compact_results = !compact_results"/>

            </v-col>
          </v-row>
        </v-card-title>
        <v-card-text>
          <v-text-field variant="outlined" v-model="search2"></v-text-field>
          <v-card variant="outlined" density="compact" class="mt-2" v-for="card in data.rows"
                  :key="card" v-if="data">
            <v-card-item :title="card[7] + ' ' + card[0]">
              <template v-slot:subtitle>
                <v-breadcrumbs density="compact" :items="card[5]" style="padding-left: 0"/>
              </template>
            </v-card-item>
            <v-card-subtitle>
            </v-card-subtitle>
            <v-expand-transition>
              <v-card-text class="stuff" v-if="compact_results">
                <div v-html="highlight(card[3], search2)"></div>
              </v-card-text>
            </v-expand-transition>
          </v-card>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
  <v-row class="mt-5">
    <v-col>
      <v-label>Hybrid Search with RFF with K_full_text_search = .1</v-label>
      <v-card variant="outlined">

        <v-card-title>
          <v-row>
            <v-col>Search CrateDB docs</v-col>
            <v-spacer/>
            <v-col class="text-right">
              <v-btn size="small"
                     class="ml-2"
                     text="Compact results"
                     variant="tonal"
                     :prepend-icon="compact_results_0 ? 'mdi-check-circle-outline': 'mdi-circle-outline'"
                     @click="compact_results_0 = !compact_results_0"/>
            </v-col>
          </v-row>
        </v-card-title>

        <v-card-text>
          <v-text-field variant="outlined"
                        v-model="hybrid_search_options.text"
                        clearable
                        @click:clear="hybrid_search_options.results = []"/>

          <v-card variant="outlined" density="compact" class="mt-2"
                  v-for="card in hybrid_search_options.results.rows"
                  :key="card" v-if="hybrid_search_options.results.rows">

            <v-card-item>
              <template v-slot:title>
                {{ card[0] + ' ' }} <a :href="card[5]" target="_blank">
                <v-icon icon="mdi-link-variant"/>
              </a>
              </template>
              <template v-slot:subtitle>
                <v-breadcrumbs density="compact" :items="card[4]" style="padding-left: 0"/>
              </template>
            </v-card-item>


            <v-expand-transition>
              <v-card-text class="stuff" v-if="compact_results_0">
                <div v-html="highlight(card[3], hybrid_search_options.text)"></div>
              </v-card-text>
            </v-expand-transition>

          </v-card>

        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</v-container>
</template>

<style>
.stuff p {
  padding-top: 15px
}

.stuff .admonition p {
  margin-top: 10 !important;
  padding-top: 0 !important;
}

.stuff li {
  margin-left: 20px
}

.stuff {
  margin-top: -35px
}

.stuff thead {
  text-align: left;
}

.stuff tr {
  vertical-align: center;
}

.stuff table {
  padding: 5px
}

.stuff table td {
  padding-left: 5px;
  padding-right: 5px
}

tr:hover td {
  background: rgba(176, 176, 176, 0.08)
}

.stuff .admonition {
  padding: 15px;
}

.caution {
  outline: 1px solid red;
  margin-top: 10px;

}

.note {
  margin-top: 10px;
  outline: 1px solid #3d3dfd;
}

.seealso {
  margin-top: 10px;
  outline: 1px solid darkgreen;
}

.admonition-title {
  font-size: 20px;
  margin-top: 5px;
  margin-bottom: 15px;
  font-weight: bold;
}


.stuff .highlight {
  margin-top: 10px;
  padding: 10px;
  background-color: rgba(162, 162, 162, 0.18);
}

code {
  padding: 1px;
  background-color: rgba(162, 162, 162, 0.18);
}
</style>

