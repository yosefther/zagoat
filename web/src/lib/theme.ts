export type ThemeChoice = "auto" | "light" | "dark";

export const THEME_STORAGE_KEY = "zagoat-theme";

/** Runs inline in <head> before first paint, so a saved theme never flashes. */
export const THEME_BOOT_SCRIPT = `(function(){try{var t=localStorage.getItem(${JSON.stringify(
  THEME_STORAGE_KEY,
)});if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t)}catch(e){}})()`;
