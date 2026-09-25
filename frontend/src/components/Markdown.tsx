import DOMPurify from 'dompurify'
import { marked } from 'marked'

/**
 * 把模型返回的 Markdown 渲染成 HTML（对应 PRD 的 F21）。
 *
 * 两步都不能少：
 *   1. marked          —— 把 Markdown 转成 HTML（模型回答里带 **加粗**、列表等）
 *   2. DOMPurify.sanitize —— 洗掉危险标签和属性
 *
 * 第 2 步不能省：这段内容来自大模型（阶段二还会来自知识库文档），
 * 都属于不可信输入。把未消毒的 HTML 交给 dangerouslySetInnerHTML
 * 是最典型的 XSS 入口。（PRD §8.2 第 16 项专门点了这一条）
 */
export default function Markdown({ text }: { text: string }) {
  const html = DOMPurify.sanitize(marked.parse(text) as string)

  return <div className="markdown-body" dangerouslySetInnerHTML={{ __html: html }} />
}
