import React from "react";

type ReactMarkdownProps = {
  children: string;
  compact?: boolean;
};

function renderInline(text: string): React.ReactNode[] {
  const parts = text.split(/(\[.*?\]\(.*?\)|\*\*.+?\*\*)/g).filter(Boolean);

  return parts.map((part, index) => {
    const linkMatch = part.match(/^\[(.*?)\]\((.*?)\)$/);
    if (linkMatch) {
      const [, label, href] = linkMatch;
      return (
        <a
          key={`${href}-${index}`}
          href={href}
          className="font-medium text-teal-700 underline underline-offset-2 hover:text-teal-800"
          target={href.startsWith("http") ? "_blank" : undefined}
          rel={href.startsWith("http") ? "noreferrer" : undefined}
        >
          {label}
        </a>
      );
    }

    const strongMatch = part.match(/^\*\*(.+?)\*\*$/);
    if (strongMatch) {
      return <strong key={`strong-${index}`} className="font-semibold text-[#041627]">{strongMatch[1]}</strong>;
    }

    return <React.Fragment key={`text-${index}`}>{part}</React.Fragment>;
  });
}

export function ReactMarkdown({ children, compact = false }: ReactMarkdownProps) {
  const lines = children.split(/\r?\n/);
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (!listItems.length) {
      return;
    }

    elements.push(
      <ul key={`list-${elements.length}`} className="mb-4 list-disc space-y-2 pl-6 text-slate-700">
        {listItems.map((item, index) => (
          <li key={`item-${index}`}>{renderInline(item)}</li>
        ))}
      </ul>,
    );
    listItems = [];
  };

  lines.forEach((rawLine, index) => {
    const line = rawLine.trim();

    if (!line) {
      flushList();
      return;
    }

    if (line.startsWith("- ") || line.startsWith("* ")) {
      listItems.push(line.slice(2).trim());
      return;
    }

    flushList();

    if (line.startsWith("### ")) {
      elements.push(
        <h3 key={`h3-${index}`} className="mt-8 mb-3 text-xl font-semibold text-[#041627]">
          {renderInline(line.slice(4))}
        </h3>,
      );
      return;
    }

    if (line.startsWith("## ")) {
      elements.push(
        <h2 key={`h2-${index}`} className="mt-10 mb-4 text-2xl font-semibold text-[#041627]">
          {renderInline(line.slice(3))}
        </h2>,
      );
      return;
    }

    if (line.startsWith("# ")) {
      elements.push(
        <h1 key={`h1-${index}`} className="mt-12 mb-5 text-3xl font-bold text-[#041627]">
          {renderInline(line.slice(2))}
        </h1>,
      );
      return;
    }

    if (line === "---") {
      elements.push(<hr key={`hr-${index}`} className="my-8 border-slate-200" />);
      return;
    }

    if (line.startsWith("> ")) {
      elements.push(
        <blockquote
          key={`quote-${index}`}
          className="mb-4 border-l-4 border-teal-500 bg-teal-50 px-4 py-3 text-slate-700"
        >
          {renderInline(line.slice(2))}
        </blockquote>,
      );
      return;
    }

    elements.push(
      <p key={`p-${index}`} className="mb-4 leading-7 text-slate-700">
        {renderInline(line)}
      </p>,
    );
  });

  flushList();

  return <article className={compact ? "max-w-none [&>p:last-child]:mb-0" : "mx-auto max-w-4xl px-4 py-8 md:px-6"}>{elements}</article>;
}
