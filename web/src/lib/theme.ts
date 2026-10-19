export type Theme = "light" | "dark";

export const THEME_STORAGE_KEY = "zagoat-theme";
export const DEFAULT_THEME: Theme = "dark";

/** Runs inline in <head> before first paint, so a saved light theme never flashes dark. */
export const THEME_BOOT_SCRIPT = `(function(){try{var t=localStorage.getItem(${JSON.stringify(
  THEME_STORAGE_KEY,
)});if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t)}catch(e){}})()`;
