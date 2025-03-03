<script setup>
const objs = [
  {id: 1, name: 'test'},
  {id: 2, name: 'test'},
  {id: 3, name: 'test'},
  {id: 4, name: 'test'},
  {id: 5, name: 'test'},
  {id: 6, name: 'test'},
]
</script>

<template>
  <slot name="input">
    <input>
  </slot>
  <slot name="button">
    <button>submit</button>
  </slot>
  <slot name="content"
        :results="objs">
    <div v-for="obj in objs">
      {{ obj }}
    </div>
  </slot>
</template>

<style scoped>

</style>
