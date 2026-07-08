import React, { useEffect, useRef } from "react";

export default function HtmlWidget({ html, className = "", id }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return undefined;

    mount.innerHTML = html;

    let cancelled = false;

    const runScripts = async () => {
      const scripts = Array.from(mount.querySelectorAll("script"));

      for (const oldScript of scripts) {
        if (cancelled) return;

        const script = document.createElement("script");

        for (const { name, value } of Array.from(oldScript.attributes)) {
          script.setAttribute(name, value);
        }

        const isExternal = Boolean(script.src);
        const parent = oldScript.parentNode;
        if (!parent) continue;

        const replacement = document.createElement("span");
        parent.replaceChild(replacement, oldScript);

        if (isExternal) {
          await new Promise((resolve, reject) => {
            script.async = false;
            script.onload = () => resolve();
            script.onerror = () => reject(new Error(`Failed to load ${script.src}`));
            script.text = oldScript.textContent ?? "";
            replacement.replaceWith(script);
          });
        } else {
          script.text = oldScript.textContent ?? "";
          replacement.replaceWith(script);
        }
      }
    };

    void runScripts();

    return () => {
      cancelled = true;
      mount.innerHTML = "";
    };
  }, [html]);

  return <div ref={mountRef} id={id} className={className} />;
}
