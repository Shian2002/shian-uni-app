/**
 * Patch vue.runtime.esm.js — Fix "Cannot assign to read only property '_'" slot error
 *
 * 根因: initSlots 中 def(children, "_", type) 将 _ 属性设为只读,
 * 而 updateSlots 中 extend(slots, children) (= Object.assign)
 * 试图复制 _ 属性到同一个底层对象, 在严格模式下抛出 TypeError.
 *
 * 修复: 在 updateSlots 中将 extend(slots, children) 替换为 safeExtend,
 * 跳过 _ 属性 (该属性在 initSlots 中已正确处理).
 */

const fs = require('fs');

const files = [
  'node_modules/@dcloudio/uni-h5-vue/dist/vue.runtime.esm.js',
  'node_modules/@dcloudio/uni-h5-vue/dist-x/vue.runtime.esm.js',
];

let totalPatched = 0;
let totalFail = 0;

files.forEach(fp => {
  try {
    if (!fs.existsSync(fp)) {
      console.log(`[SKIP] ${fp} not found`);
      return;
    }

    let content = fs.readFileSync(fp, 'utf8');

    if (content.indexOf('// PATCHED vue-slot: safeExtend') >= 0) {
      console.log(`[OK] ${fp} already patched`);
      totalPatched++;
      return;
    }

    // Replace: extend(slots, children) within updateSlots context
    // The "extend" is Object.assign, and children may have read-only "_" property
    // We replace with a safe version that skips "_"
    //
    // Pattern: we find "extend(slots, children)" that appears in updateSlots
    // There are 2 occurrences: line ~5859 (HMR) and line ~5864 (main path)
    //
    // We use a distinctive marker to avoid re-patching

    let count = 0;
    const marker = '// PATCHED vue-slot: safeExtend';
    // Match: extend(slots, children) — the specific pattern in updateSlots
    // Replace with a safe version
    const pattern = /extend\(slots,\s*children\)/g;
    content = content.replace(pattern, (match) => {
      count++;
      return `(function(){try{Object.assign(slots,children)}catch(__e){for(var __k in children){if(__k!=='_')slots[__k]=children[__k]}}})()`;
    });

    if (count > 0) {
      // Add marker
      content = content.replace(
        'const updateSlots = (instance, children, optimized) => {',
        `const updateSlots = (instance, children, optimized) => { ${marker}`
      );
      fs.writeFileSync(fp, content, 'utf8');
      console.log(`[OK] ${fp} patched (${count} replacements)`);
      totalPatched++;
    } else {
      console.log(`[WARN] ${fp}: extend(slots, children) pattern not found`);
      totalFail++;
    }
  } catch (e) {
    console.log(`[ERROR] ${fp}: ${e.message}`);
    totalFail++;
  }
});

if (totalFail === 0) {
  console.log(`Patch vue-slot applied successfully! (${totalPatched} files)`);
} else {
  console.log(`Patch vue-slot completed with ${totalFail} failures (${totalPatched} OK)`);
}
