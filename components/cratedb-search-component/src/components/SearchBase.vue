<script setup>
const model = defineModel()
</script>

<template>
  <div>
    <slot name="input">
      <input>
    </slot>
    <slot name="button">
      <button>submit</button>
    </slot>
    <slot name="content"
          :results="model">
      <div v-for="obj in model">
        {{ obj }}
      </div>
    </slot>
  </div>
</template>

<style scoped>

</style>
