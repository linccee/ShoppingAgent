import { Fragment, type ReactNode } from 'react';

import styles from './MarkdownContent.module.css';

interface MarkdownContentProps {
  content: string;
}

type Block =
  | { type: 'heading'; level: 1 | 2 | 3 | 4 | 5 | 6; content: string }
  | { type: 'paragraph'; content: string }
  | { type: 'unordered-list'; items: string[] }
  | { type: 'ordered-list'; items: string[] }
  | { type: 'code'; content: string; language: string | null }
  | { type: 'blockquote'; content: string }
  | { type: 'hr' };

const HEADING_PATTERN = /^(#{1,6})\s+(.+)$/;
const UNORDERED_LIST_PATTERN = /^\s*[-*+]\s+(.*)$/;
const ORDERED_LIST_PATTERN = /^\s*\d+\.\s+(.*)$/;
const BLOCKQUOTE_PATTERN = /^\s*>\s?(.*)$/;
const CODE_FENCE_PATTERN = /^```([\w-]+)?\s*$/;
const THEMATIC_BREAK_PATTERN = /^\s*(?:---|\*\*\*|___)\s*$/;

function isBlockStart(line: string): boolean {
  return (
    line.trim() === '' ||
    HEADING_PATTERN.test(line) ||
    UNORDERED_LIST_PATTERN.test(line) ||
    ORDERED_LIST_PATTERN.test(line) ||
    BLOCKQUOTE_PATTERN.test(line) ||
    CODE_FENCE_PATTERN.test(line) ||
    THEMATIC_BREAK_PATTERN.test(line)
  );
}

function collectListItems(
  lines: string[],
  startIndex: number,
  pattern: RegExp,
): { items: string[]; nextIndex: number } {
  const items: string[] = [];
  let index = startIndex;

  while (index < lines.length) {
    const match = lines[index]?.match(pattern);
    if (!match) {
      break;
    }

    const parts = [match[1].trim()];
    index += 1;

    while (
      index < lines.length &&
      lines[index].trim() !== '' &&
      !isBlockStart(lines[index]) &&
      /^\s{2,}\S/.test(lines[index])
    ) {
      parts.push(lines[index].trim());
      index += 1;
    }

    items.push(parts.join(' '));
  }

  return { items, nextIndex: index };
}

function parseMarkdown(content: string): Block[] {
  const normalized = content.replace(/\r\n/g, '\n');
  const lines = normalized.split('\n');
  const blocks: Block[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    const trimmed = line.trim();

    if (!trimmed) {
      index += 1;
      continue;
    }

    const fenceMatch = line.match(CODE_FENCE_PATTERN);
    if (fenceMatch) {
      const codeLines: string[] = [];
      const language = fenceMatch[1] ?? null;
      index += 1;

      while (index < lines.length && !CODE_FENCE_PATTERN.test(lines[index])) {
        codeLines.push(lines[index]);
        index += 1;
      }

      if (index < lines.length) {
        index += 1;
      }

      blocks.push({
        type: 'code',
        content: codeLines.join('\n'),
        language,
      });
      continue;
    }

    const headingMatch = line.match(HEADING_PATTERN);
    if (headingMatch) {
      blocks.push({
        type: 'heading',
        level: headingMatch[1].length as 1 | 2 | 3 | 4 | 5 | 6,
        content: headingMatch[2].trim(),
      });
      index += 1;
      continue;
    }

    if (THEMATIC_BREAK_PATTERN.test(line)) {
      blocks.push({ type: 'hr' });
      index += 1;
      continue;
    }

    if (UNORDERED_LIST_PATTERN.test(line)) {
      const { items, nextIndex } = collectListItems(lines, index, UNORDERED_LIST_PATTERN);
      blocks.push({ type: 'unordered-list', items });
      index = nextIndex;
      continue;
    }

    if (ORDERED_LIST_PATTERN.test(line)) {
      const { items, nextIndex } = collectListItems(lines, index, ORDERED_LIST_PATTERN);
      blocks.push({ type: 'ordered-list', items });
      index = nextIndex;
      continue;
    }

    if (BLOCKQUOTE_PATTERN.test(line)) {
      const quoteLines: string[] = [];

      while (index < lines.length) {
        const match = lines[index]?.match(BLOCKQUOTE_PATTERN);
        if (!match) {
          break;
        }
        quoteLines.push(match[1]);
        index += 1;
      }

      blocks.push({
        type: 'blockquote',
        content: quoteLines.join(' ').trim(),
      });
      continue;
    }

    const paragraphLines = [trimmed];
    index += 1;

    while (index < lines.length && lines[index].trim() !== '' && !isBlockStart(lines[index])) {
      paragraphLines.push(lines[index].trim());
      index += 1;
    }

    blocks.push({
      type: 'paragraph',
      content: paragraphLines.join(' '),
    });
  }

  return blocks;
}

function findInlineMatch(source: string):
  | {
      kind: 'link' | 'code' | 'strong' | 'emphasis';
      index: number;
      length: number;
      text: string;
      href?: string;
    }
  | null {
  const patterns: Array<{
    kind: 'link' | 'code' | 'strong' | 'emphasis';
    regex: RegExp;
  }> = [
    { kind: 'link', regex: /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/ },
    { kind: 'code', regex: /`([^`]+)`/ },
    { kind: 'strong', regex: /\*\*([^*]+)\*\*/ },
    { kind: 'emphasis', regex: /\*([^*\n]+)\*/ },
  ];

  let bestMatch:
    | {
        kind: 'link' | 'code' | 'strong' | 'emphasis';
        index: number;
        length: number;
        text: string;
        href?: string;
      }
    | null = null;

  for (const pattern of patterns) {
    const match = source.match(pattern.regex);
    if (!match || match.index === undefined) {
      continue;
    }

    if (bestMatch && match.index >= bestMatch.index) {
      continue;
    }

    bestMatch = {
      kind: pattern.kind,
      index: match.index,
      length: match[0].length,
      text: match[1],
      href: pattern.kind === 'link' ? match[2] : undefined,
    };
  }

  return bestMatch;
}

function renderInline(content: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let remaining = content;
  let index = 0;

  while (remaining) {
    const match = findInlineMatch(remaining);

    if (!match) {
      nodes.push(<Fragment key={`${keyPrefix}-text-${index}`}>{remaining}</Fragment>);
      break;
    }

    if (match.index > 0) {
      nodes.push(
        <Fragment key={`${keyPrefix}-text-${index}`}>
          {remaining.slice(0, match.index)}
        </Fragment>,
      );
      index += 1;
    }

    const innerKey = `${keyPrefix}-${match.kind}-${index}`;
    if (match.kind === 'link') {
      nodes.push(
        <a
          key={innerKey}
          className={styles.link}
          href={match.href}
          target="_blank"
          rel="noreferrer"
        >
          {renderInline(match.text, `${innerKey}-label`)}
        </a>,
      );
    } else if (match.kind === 'code') {
      nodes.push(
        <code key={innerKey} className={styles.inlineCode}>
          {match.text}
        </code>,
      );
    } else if (match.kind === 'strong') {
      nodes.push(
        <strong key={innerKey} className={styles.strong}>
          {renderInline(match.text, `${innerKey}-strong`)}
        </strong>,
      );
    } else {
      nodes.push(
        <em key={innerKey} className={styles.emphasis}>
          {renderInline(match.text, `${innerKey}-em`)}
        </em>,
      );
    }

    remaining = remaining.slice(match.index + match.length);
    index += 1;
  }

  return nodes;
}

function renderBlock(block: Block, index: number): ReactNode {
  switch (block.type) {
    case 'heading': {
      const Tag = `h${block.level}` as const;
      return (
        <Tag key={`heading-${index}`} className={styles[`h${block.level}`]}>
          {renderInline(block.content, `heading-${index}`)}
        </Tag>
      );
    }
    case 'paragraph':
      return (
        <p key={`paragraph-${index}`} className={styles.paragraph}>
          {renderInline(block.content, `paragraph-${index}`)}
        </p>
      );
    case 'unordered-list':
      return (
        <ul key={`ul-${index}`} className={styles.list}>
          {block.items.map((item, itemIndex) => (
            <li key={`ul-${index}-${itemIndex}`} className={styles.listItem}>
              {renderInline(item, `ul-${index}-${itemIndex}`)}
            </li>
          ))}
        </ul>
      );
    case 'ordered-list':
      return (
        <ol key={`ol-${index}`} className={styles.list}>
          {block.items.map((item, itemIndex) => (
            <li key={`ol-${index}-${itemIndex}`} className={styles.listItem}>
              {renderInline(item, `ol-${index}-${itemIndex}`)}
            </li>
          ))}
        </ol>
      );
    case 'blockquote':
      return (
        <blockquote key={`blockquote-${index}`} className={styles.blockquote}>
          <p className={styles.blockquoteText}>
            {renderInline(block.content, `blockquote-${index}`)}
          </p>
        </blockquote>
      );
    case 'code':
      return (
        <pre key={`code-${index}`} className={styles.codeBlock}>
          <code data-language={block.language ?? undefined}>{block.content}</code>
        </pre>
      );
    case 'hr':
      return <hr key={`hr-${index}`} className={styles.hr} />;
    default:
      return null;
  }
}

export function MarkdownContent({ content }: MarkdownContentProps) {
  const blocks = parseMarkdown(content);

  if (blocks.length === 0) {
    return null;
  }

  return <div className={styles.root}>{blocks.map(renderBlock)}</div>;
}
