import { useMemo } from "react";
import { tileDocument, type TileName } from "@/lib/tiles";

export function TileArt({
  name,
  size,
  radius = 14,
}: {
  name: TileName;
  size: number;
  radius?: number;
}) {
  const srcDoc = useMemo(() => tileDocument(name), [name]);
  const scale = size / 512;
  return (
    <div className="tile-art" style={{ width: size, height: size, borderRadius: radius }}>
      <iframe
        title=""
        tabIndex={-1}
        scrolling="no"
        srcDoc={srcDoc}
        style={{ transform: `scale(${scale})` }}
      />
    </div>
  );
}
