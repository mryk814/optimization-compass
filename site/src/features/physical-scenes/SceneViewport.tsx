import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import type { SceneDrawing, Vec3 } from "./types";

const vector = (p: Vec3) => new THREE.Vector3(...p);
type CameraView = "perspective" | "front" | "top";
interface ViewHandle { view(preset: CameraView): void; key(event: KeyboardEvent): void }

/** A single on-demand renderer. Camera movement never changes the calculated state. */
export function SceneViewport({ drawing, label }: { drawing: SceneDrawing; label: string }) {
  const host = useRef<HTMLDivElement>(null);
  const handle = useRef<ViewHandle | null>(null);
  const update = useRef<((drawing: SceneDrawing) => void) | null>(null);
  const latest = useRef(drawing);
  latest.current = drawing;
  const [available, setAvailable] = useState(true);
  useEffect(() => {
    const element = host.current;
    if (!element) return;
    let renderer: THREE.WebGLRenderer;
    try {
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("webgl2", { antialias: true, alpha: false });
      if (!context) { setAvailable(false); return; }
      renderer = new THREE.WebGLRenderer({ canvas, context, antialias: true, alpha: false });
    }
    catch { setAvailable(false); return; }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.setClearColor("#f5f8f8");
    element.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    scene.add(new THREE.HemisphereLight(0xffffff, 0x8998a8, 2));
    const light = new THREE.DirectionalLight(0xffffff, 2.2);
    light.position.set(3, -4, 6);
    scene.add(light);
    const camera = new THREE.PerspectiveCamera(38, 1, 0.01, 500);
    camera.up.set(0, 0, 1);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = false;
    controls.enablePan = false;
    controls.minDistance = 0.3;
    controls.maxDistance = 150;
    const objects = new THREE.Group();
    let fit = 1;
    scene.add(objects);
    const render = () => renderer.render(scene, camera);
    controls.addEventListener("change", render);
    const disposeObjects = () => {
      objects.traverse((object) => {
        if (object instanceof THREE.Mesh || object instanceof THREE.Line) {
          if (object instanceof THREE.InstancedMesh) object.dispose();
          object.geometry.dispose();
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((material) => material.dispose());
        }
      });
      objects.clear();
    };
    const view = (preset: CameraView) => {
      const { center, radius } = latest.current;
      const target = vector(center);
      const direction = preset === "front" ? new THREE.Vector3(0, -1, 0.001)
        : preset === "top" ? new THREE.Vector3(0.001, -0.001, 1) : new THREE.Vector3(1.5, -2.5, 1.6);
      const distance = radius * 1.08 / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2));
      camera.position.copy(target).add(direction.normalize().multiplyScalar(distance * fit));
      controls.target.copy(target);
      controls.update();
      render();
    };
    const material = (color: string, opacity = 1) => new THREE.MeshStandardMaterial({
      color, roughness: 1, metalness: 0, transparent: opacity < 1, opacity, depthWrite: opacity === 1,
    });
    update.current = (next) => {
      disposeObjects();
      for (const box of next.boxes ?? []) {
        const mesh = new THREE.Mesh(new THREE.BoxGeometry(...box.size), material(box.color, box.opacity));
        mesh.position.copy(vector(box.center)); objects.add(mesh);
      }
      for (const sphere of next.spheres ?? []) {
        const mesh = new THREE.Mesh(new THREE.SphereGeometry(sphere.radius, 24, 16), material(sphere.color, sphere.opacity));
        mesh.position.copy(vector(sphere.center)); objects.add(mesh);
      }
      for (const rod of next.rods ?? []) {
        const start = vector(rod.from); const end = vector(rod.to); const delta = end.clone().sub(start);
        const mesh = new THREE.Mesh(new THREE.CylinderGeometry(rod.radius, rod.radius, delta.length(), 12), material(rod.color));
        mesh.position.copy(start.add(end).multiplyScalar(0.5));
        mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.normalize());
        objects.add(mesh);
      }
      for (const line of next.lines ?? []) {
        if (line.points.length < 2) continue;
        const geometry = new THREE.BufferGeometry().setFromPoints(line.points.map(vector));
        const mesh = new THREE.Line(geometry, line.dashed
          ? new THREE.LineDashedMaterial({ color: line.color, dashSize: 0.12, gapSize: 0.06 })
          : new THREE.LineBasicMaterial({ color: line.color }));
        if (line.dashed) mesh.computeLineDistances();
        objects.add(mesh);
      }
      for (const arrow of next.arrows ?? []) {
        objects.add(new THREE.ArrowHelper(vector(arrow.direction).normalize(), vector(arrow.from), arrow.length, arrow.color, arrow.length * 0.25, arrow.length * 0.15));
      }
      if (next.surface?.positions.length) {
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute("position", new THREE.Float32BufferAttribute(next.surface.positions, 3));
        geometry.computeVertexNormals();
        objects.add(new THREE.Mesh(geometry, material(next.surface.color)));
      }
      if (!next.surface && next.voxels && next.voxels.centers.length) {
        const { centers, colors, size } = next.voxels;
        const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(...size), material("#ffffff"), centers.length);
        centers.forEach((center, index) => {
          mesh.setMatrixAt(index, new THREE.Matrix4().makeTranslation(...center));
          mesh.setColorAt(index, new THREE.Color(colors[index]));
        });
        mesh.instanceMatrix.needsUpdate = true;
        if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
        objects.add(mesh);
      }
      render();
    };
    handle.current = { view, key(event) {
      const offset = camera.position.clone().sub(controls.target);
      const spherical = new THREE.Spherical().setFromVector3(new THREE.Vector3(offset.x, offset.z, offset.y));
      if (event.key === "ArrowLeft") spherical.theta -= 0.12;
      else if (event.key === "ArrowRight") spherical.theta += 0.12;
      else if (event.key === "ArrowUp") spherical.phi -= 0.12;
      else if (event.key === "ArrowDown") spherical.phi += 0.12;
      else if (event.key === "+" || event.key === "=") spherical.radius *= 0.9;
      else if (event.key === "-") spherical.radius *= 1.1;
      else return;
      event.preventDefault();
      spherical.phi = Math.max(0.05, Math.min(Math.PI - 0.05, spherical.phi));
      spherical.radius = Math.max(0.3, Math.min(150, spherical.radius));
      offset.setFromSpherical(spherical);
      camera.position.copy(controls.target).add(new THREE.Vector3(offset.x, offset.z, offset.y));
      controls.update(); render();
    } };
    const resize = () => {
      const width = element.clientWidth; const height = element.clientHeight;
      if (!width || !height) return;
      camera.aspect = width / height; camera.updateProjectionMatrix();
      const halfFov = THREE.MathUtils.degToRad(camera.fov / 2);
      const nextFit = Math.max(1, Math.sin(halfFov) / Math.sin(Math.atan(Math.tan(halfFov) * camera.aspect)));
      camera.position.sub(controls.target).multiplyScalar(nextFit / fit).add(controls.target);
      fit = nextFit;
      controls.update();
      renderer.setSize(width, height); render();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(element);
    const lost = (event: Event) => { event.preventDefault(); setAvailable(false); };
    renderer.domElement.addEventListener("webglcontextlost", lost);
    update.current(latest.current); view("perspective"); resize();
    return () => {
      observer.disconnect(); controls.dispose(); disposeObjects();
      renderer.domElement.removeEventListener("webglcontextlost", lost);
      renderer.dispose(); renderer.domElement.remove(); handle.current = null; update.current = null;
    };
  }, []);
  useEffect(() => { update.current?.(drawing); }, [drawing]);
  return <div className="physical-viewport-wrap">
    <div className="physical-view-tools" aria-label="視点の操作">
      <button type="button" onClick={() => handle.current?.view("perspective")}>視点を戻す</button>
      <button type="button" onClick={() => handle.current?.view("front")}>横から</button>
      <button type="button" onClick={() => handle.current?.view("top")}>上から</button>
    </div>
    <div ref={host} className="physical-viewport" role="group" aria-label={label} tabIndex={0}
      onKeyDown={(event) => handle.current?.key(event)}>
      {!available && <p className="physical-webgl-fallback">3D表示を利用できません。同じ計算結果を下の2D図と数値で確認できます。</p>}
    </div>
    <p className="physical-camera-hint">ドラッグで回転、ホイールで拡大。図にフォーカスして矢印キー、＋／−でも操作できます。</p>
  </div>;
}
