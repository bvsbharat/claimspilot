import { useEffect } from "react";

interface KeyboardShortcutOptions {
  key: string;
  shift?: boolean;
  ctrl?: boolean;
  alt?: boolean;
  meta?: boolean;
}

export function useKeyboardShortcut(
  options: KeyboardShortcutOptions,
  callback: () => void
) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const matchesKey = event.key.toLowerCase() === options.key.toLowerCase();
      const matchesShift = options.shift ? event.shiftKey : !event.shiftKey;
      const matchesCtrl = options.ctrl ? event.ctrlKey : !event.ctrlKey;
      const matchesAlt = options.alt ? event.altKey : !event.altKey;
      const matchesMeta = options.meta ? event.metaKey : !event.metaKey;

      // For shift-only shortcuts, we want to allow shift but not other modifiers
      if (options.shift && !options.ctrl && !options.alt && !options.meta) {
        if (
          matchesKey &&
          event.shiftKey &&
          !event.ctrlKey &&
          !event.altKey &&
          !event.metaKey
        ) {
          event.preventDefault();
          callback();
        }
      } else if (
        matchesKey &&
        matchesShift &&
        matchesCtrl &&
        matchesAlt &&
        matchesMeta
      ) {
        event.preventDefault();
        callback();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [options, callback]);
}
