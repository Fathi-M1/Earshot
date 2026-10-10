import tokens from "../../../design/tokens.json";

export const brand = tokens.brand;

// FLAG: `git remote get-url origin` failed. This repo has no remotes.
// Replace REPO_URL with the real GitHub repository before treating these links as live.
export const REPO_URL = "https://github.com/REPLACE_WITH_ORIGIN/earshot";
export const githubUrl = REPO_URL;

export const contactEmail = "fatximahadpoqor1@gmail.com";

export const captions = [
  "Boarding for flight 5J 812 now at gate\u00A014.",
  "Lilipat ang meeting sa Lunes ng alas-diyes.",
  "الاجتماع يوم الاثنين الساعة العاشرة",
  "Fathi, can you take the next point?",
];

export const languages = [
  { code: "EN", line: "Next station, Ayala.", dir: "ltr" as const },
  { code: "TL", line: "Saan ang gate natin?", dir: "ltr" as const },
  { code: "AR", line: "الرحلة متأخرة نصف ساعة", dir: "rtl" as const },
];
