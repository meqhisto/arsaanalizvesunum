/* Auto-generated from base_main.html */
import React from "react";

export const rawHtml = "";

export default function BaseMain(props: { html?: string; wrapperClassName?: string }) {
  const { html = rawHtml, wrapperClassName } = props;
  return (
    <div className={wrapperClassName} dangerouslySetInnerHTML={{ __html: html }} />
  );
}
