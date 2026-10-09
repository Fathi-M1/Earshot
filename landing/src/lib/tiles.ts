import alertHtml from "../../../design/tiles/alert.html?raw";
import catchHtml from "../../../design/tiles/catch-up.html?raw";
import listeningHtml from "../../../design/tiles/listening.html?raw";
import mutedHtml from "../../../design/tiles/muted.html?raw";

const tiles = {
  alert: alertHtml,
  catchup: catchHtml,
  listening: listeningHtml,
  muted: mutedHtml,
} as const;

export type TileName = keyof typeof tiles;

export function tileDocument(name: TileName) {
  return tiles[name]
    .replaceAll(
      "../fonts/HostGrotesk-VariableFont_wght.ttf",
      "/fonts/HostGrotesk-VariableFont_wght.ttf",
    )
    .replaceAll(
      "../fonts/FragmentMono-Regular.ttf",
      "/fonts/FragmentMono-Regular.ttf",
    );
}
