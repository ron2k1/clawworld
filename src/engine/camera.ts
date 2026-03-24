export class Camera {
  x = 0;
  y = 0;
  private viewWidth: number;
  private viewHeight: number;
  private lerp: number;

  constructor(viewWidth: number, viewHeight: number, lerp = 0.18) {
    this.viewWidth = viewWidth;
    this.viewHeight = viewHeight;
    this.lerp = lerp;
  }

  follow(targetX: number, targetY: number, mapPixelW: number, mapPixelH: number): void {
    const idealX = targetX - this.viewWidth / 2;
    const idealY = targetY - this.viewHeight / 2;
    this.x += (idealX - this.x) * this.lerp;
    this.y += (idealY - this.y) * this.lerp;
    // Clamp to map bounds
    this.x = Math.round(Math.max(0, Math.min(this.x, mapPixelW - this.viewWidth)));
    this.y = Math.round(Math.max(0, Math.min(this.y, mapPixelH - this.viewHeight)));
  }
}
