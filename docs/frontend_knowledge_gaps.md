# Morrow 前端 · 原生三件套待补知识点

> **本文档是临时的**：读完把缺的折进 `2 Fullstack Dev/24 Frontend Dev/` 对应笔记，然后直接删掉它。
> **怎么来的**：把该目录下三份笔记（`1.HTML.md` / `2.CSS.md` / `3.Javascript.md`）逐条比对"Morrow 阶段一前端实际要做的功能"得出。**只列本项目用得到、而笔记里没有的**；笔记里已有的（HTML 结构 / 表单 / 区块；CSS 选择器 / 盒子模型 / Flex / 定位 / 浮动；JS 变量 / 条件 / 循环 / 函数 / 闭包 / 事件基础 / DOM 基础）不重复。
> **背景**：阶段一前端已定为原生 HTML + CSS + JS，无框架、无构建、无 npm（见 [v1 PRD §0.3](v1_prd.md)）。

分三档：**A 必须补**（不补写不动）/ **B 强烈建议**（决定代码好不好读、好不好改）/ **C 可选**。

---

## A. JavaScript —— 必须补（这是最大的一块）

### A1. `fetch` + `Promise` + `async/await`

笔记里完全没有。整个前端就是围绕它转：本项目一共 7 个接口要调。

要点：`fetch` 返回 Promise，而且要 `await` **两次**（第一次拿到响应，第二次才拿到 JSON）；**`fetch` 对 401 / 500 不会报错**，它只在网络断掉时 reject。

```js
const res = await fetch('/api/v1/conversations', { headers: { Authorization: `Bearer ${token}` } });
if (!res.ok) { /* 这里必须自己判断，fetch 不会帮你抛错 */ }
const json = await res.json();
```

**用在**：注册、登录、取当前用户、会话列表、新建 / 重命名 / 删除会话、消息历史、发消息。

### A2. `try/catch` 与错误处理

承接 A1：既然 `fetch` 不帮你抛 HTTP 错误，那"接口失败"就得靠 `res.ok` 自己判断。两条路径要分清——网络错误走 `catch`，业务错误走 `res.ok` + 拆统一信封的 `code`。

**用在**：401 清 token 跳登录、409「用户名已存在」、422 参数校验、502 上游模型失败。

### A3. `JSON.parse` / `JSON.stringify` + `localStorage`

笔记里完全没有。token 和用户信息要存住（刷新页面不能掉登录），而 `localStorage` 只能存字符串，所以存的时候 `JSON.stringify`、取的时候 `JSON.parse`。

**用在**：登录态持久化、刷新页面恢复。

### A4. 数组方法：`map` / `filter` / `find` / `join` / `push`

笔记里只有 `for` / `while` 循环。渲染列表的标准写法是 `map` 出数组再 `join` 成字符串；删一条会话是 `filter`。

**用在**：几乎所有列表渲染（会话列表、消息列表）。

### A5. 模板字符串（`` `${}` ``）

笔记里拼字符串用的是 `+`。拼 HTML 用模板字符串才读得下去，而且能直接换行。

**同时要建立意识**：凡是"把数据拼进 HTML 字符串"，都是 XSS 入口——这就是为什么模型回答要过 `DOMPurify`。

**用在**：渲染消息气泡、会话项。

### A6. 事件对象与 `preventDefault`

笔记里的事件处理函数没有参数。要补三件：

- `event.target.value`：取输入框当前内容
- `event.preventDefault()`：表单默认提交会刷新页面、状态全丢
- `event.key === 'Enter'`：回车发送

**用在**：登录 / 注册表单、发消息输入框。

### A7. HTTP 与请求头常识

这一块是前后端对接的核心，笔记里表单那节只讲了 GET / POST 的区别。要补：

- 请求头：`Authorization: Bearer <token>`、`Content-Type: application/json`
- **`Content-Type: application/x-www-form-urlencoded`：登录接口收的是表单，不是 JSON**（OAuth2 规范要求）。用 `URLSearchParams` 拼 body。这是本项目最容易踩的一个点——同一个登录页上，注册发 JSON、登录发表单。
- 状态码语义：401 未认证 / 404 资源不存在（本项目越权也返回 404）/ 409 冲突 / 422 参数校验失败 / 502 上游失败

**用在**：全部接口调用。

### A8. `document.querySelector` / `querySelectorAll`

笔记里只有 `getElementById` / `getElementsByClassName` / `getElementsByTagName`。现代写法是 `querySelector`，参数就是你 CSS 笔记里那套选择器语法，两边正好接上。

**用在**：全部 DOM 取值。

### A9. `classList` 切换 class

笔记里改样式用的是 `element.style.color = ...`。工程上更常见的是**切 class、样式留在 CSS 里**（`classList.add / remove / toggle`）。

原生方案里"切页面""切会话"就是靠它，配合 CSS 的 `display: none`。

**用在**：登录页 ↔ 聊天页切换、切会话、显示 / 隐藏"生成中"提示。

### A10. `value` / `disabled` / `textContent` 与 `innerHTML` 的分工

- `input.value`：读输入框内容；写空串就是清空
- `button.disabled = true`：实现"生成中禁用发送"
- `textContent`：**默认选择**，防注入
- `innerHTML`：只在需要渲染 Markdown 时用，而且必须先过 `DOMPurify.sanitize`

---

## B. JavaScript —— 强烈建议

### B1. 对象字面量、解构、展开 `...`

笔记里没有。从 JSON 里取字段、复制一份数组再改都会用到，量不大但天天出现。

### B2. `var` / `let` / `const` 的作用域差异 + `for` 循环的闭包坑

笔记里既讲了 `var`/`let`/`const`，也讲了闭包，但**没把这两件事连起来**。经典坑：

```js
for (var i = 0; i < 3; i++) {
  btns[i].onclick = () => console.log(i);  // 三个按钮都打印 3
}
for (let i = 0; i < 3; i++) {
  btns[i].onclick = () => console.log(i);  // 0 1 2，正常
}
```

这是"为什么要用 `let`"最有说服力的一条。**用在**：给会话列表每一项绑删除 / 重命名按钮。

### B3. `dataset`（`data-*` 属性）

给列表里的按钮标记"我对应哪个会话 id"，比到处传变量干净。

```html
<button class="del" data-id="3">删除</button>
```

```js
btn.dataset.id;   // "3"，注意是字符串
```

**用在**：会话列表的操作按钮。

### B4. 自动滚到底：`scrollTop` / `scrollHeight`

聊天窗必备——新消息在视野外，用户以为没反应。

**用在**：消息列表。

### B5. 浏览器 DevTools 的 Network 与 Console 面板

你的调试主场：看请求头 / 请求体 / 响应体，能立刻分辨"是我没带 token"还是"后端返回错了"。

**用在**：整个联调阶段。

### B6. `<script defer>` 与"脚本执行时 DOM 是否就绪"

笔记里 `<script>` 放在 `<head>` 和 `<body>` 都有，但没讲为什么位置重要。放在 `<head>` 里又不加 `defer`，脚本会在 DOM 解析之前执行，`querySelector` 直接返回 `null`——这是原生 JS 的第一个坑。

**用在**：所有 JS 文件的引入方式。

---

## C. HTML —— 缺口很小

- **`<button>` 的 `type`**：表单里的 `button` 不写 `type` 默认是 `submit`，点一下会提交表单刷新页面。要分清 `type="button"` 与 `type="submit"`。**用在**：登录按钮、发送按钮、会话操作按钮。
- **`disabled` 属性**：与 JS 的 A10 配套。**用在**：生成中禁用输入框与发送按钮。
- **`data-*` 属性**：见 B3，属性和它是一对。
- （可选）**无障碍最小集**：`aria-live` 让"生成中"被读屏软件感知。不做不影响验收。
- 不需要管 `viewport` 适配——PRD 明确不做移动端。

---

## D. CSS —— 缺口中等

- **`box-sizing: border-box`**：笔记里没有。默认的 `content-box` 会让"宽度 100% 再加 padding"直接溢出，是最常见的布局意外。全局设一次即可。
- **`overflow` / `overflow-y: auto`**：消息区要成为独立滚动容器，否则整页滚动、输入框跟着跑。**用在**：消息列表。
- **`display: none`**：与 A9 配套，原生方案的"切页面"靠它。**用在**：登录页 / 聊天页切换。
- **`gap`**：Flex 子项间距，比给每个子项写 `margin` 干净。
- **单位 `vh` / `vw` / `%` 与 `px` 的区别**：笔记里基本只用 px（提过一次 rem）。"聊天页撑满整屏"会用到 `100vh`。
- **`white-space: pre-wrap` + `overflow-wrap: break-word`**：这两条是聊天界面的必备。不加前者，模型回答里的换行会挤成一段；不加后者，长链接会把气泡撑破。
- **`cursor: pointer` / `:disabled` 样式 / `transition`**：纯体验，可选。
- **`position: sticky`**：笔记里已讲了 `fixed`，做常驻输入框够用了，`sticky` 是补充。

---

## E. 明确不需要学（避免过度准备）

- React / TypeScript / JSX / Hooks
- Vite / npm / 打包与构建
- Ant Design 等组件库
- react-router-dom / 前端路由框架
- 媒体查询与移动端适配（PRD 明确不做）
- CSS 预处理器（Sass / Less）、Tailwind
- CSS Grid（Flex 够用，有余力再看）
- 前端测试框架
- Node.js（本项目前端完全不碰 Node）

---

## F. 动手前要一起定的两件事

1. **路由方案**：hash（`/#/chat/3`，改动最小、不用动后端）vs History API（`/chat/3` 好看，但后端要加一条兜底路由，把非 `/api` 路径都返回 `index.html`）。我倾向 **hash 起步**，等部署时再决定要不要换。
2. **JS 怎么拆文件**：单文件 vs `<script type="module">` 拆成多个。我倾向拆成 `api.js`（fetch 封装 + token + 401 收口，复用价值最高）+ `app.js`（页面与渲染）。

---

## G. 一条最小练习路径（把要补的按"能立刻用上"排好）

不用等笔记补完再动手，按这个顺序走，每一步都能在浏览器里看到结果：

1. **六十行**：一个只有输入框和按钮的页面，点一下用 `fetch` 调 `/api/v1/auth/login`，把拿到的 token `console.log` 出来。 → 覆盖 A1、A2、A3、A6、A7、A8、B6
2. **加列表**：调 `GET /conversations`，用 `map` 渲染成 `<li>`。 → 覆盖 A4、A5、A9、B1
3. **加删除**：每项一个删除按钮（`dataset` 标记 id），点击后调 `DELETE` 再重新渲染。 → 覆盖 B2、B3
4. 到这一步，聊天页剩下的只是把上面这些套路重复一遍，加上 B4 的自动滚底和 D 里的 CSS。
