const TILE_SIZE = 32;

export class Renderer {
  private ctx: CanvasRenderingContext2D;
  private tileset: HTMLImageElement | null = null;
  private tilesetColumns = 0;
  private ready = false;

  constructor(ctx: CanvasRenderingContext2D) {
    this.ctx = ctx;
    // Disable smoothing for crisp pixel art
    ctx.imageSmoothingEnabled = false;
  }

  loadTileset(src: string, columns: number): Promise<void> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        this.tileset = img;
        this.tilesetColumns = columns;
        this.ready = true;
        resolve();
      };
      img.onerror = reject;
      img.src = src;
    });
  }

  drawTile(tileId: number, destX: number, destY: number): void {
    if (!this.ready || !this.tileset || tileId <= 0) return;
    // Tiled uses 1-based IDs; convert to 0-based index
    const index = tileId - 1;
    const srcX = (index % this.tilesetColumns) * TILE_SIZE;
    const srcY = Math.floor(index / this.tilesetColumns) * TILE_SIZE;
    this.ctx.drawImage(
      this.tileset,
      srcX, srcY, TILE_SIZE, TILE_SIZE,
      destX, destY, TILE_SIZE, TILE_SIZE
    );
  }

  clear(width: number, height: number): void {
    this.ctx.clearRect(0, 0, width, height);
  }

  drawSprite(
    img: HTMLImageElement,
    frameX: number,
    frameY: number,
    frameW: number,
    frameH: number,
    destX: number,
    destY: number
  ): void {
    this.ctx.drawImage(
      img,
      frameX * frameW, frameY * frameH, frameW, frameH,
      destX, destY, frameW, frameH
    );
  }
}
