// Minh họa 3D: cánh tay robot gắp bao từ băng tải, chất lên xe container bạt (theo clip 4 của nhà sản xuất).
// Đơn vị: mét. Trục x dọc xe (đầu cabin ở x<0, cửa sau ở x=12,26), y hướng lên, z ngang xe.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const W = 1280, H = 720, DUR = 52;
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H); renderer.setPixelRatio(1);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xdfe3e6);
scene.fog = new THREE.Fog(0xdfe3e6, 45, 90);
const camera = new THREE.PerspectiveCamera(38, W / H, 0.1, 200);

scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8f94, 1.5));
const sun = new THREE.DirectionalLight(0xffffff, 2.2);
sun.position.set(-8, 22, 14); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -14, right: 22, top: 14, bottom: -14, near: 1, far: 60 });
sun.shadow.bias = -0.0006;
scene.add(sun); scene.add(sun.target); sun.target.position.set(5, 0, 0);

const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.7, metalness: 0.1, ...o });
function box(w, h, d, mat, x = 0, y = 0, z = 0, parent = scene) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; parent.add(m); return m;
}
function cyl(r, h, mat, parent, axis = 'y') {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 24), mat);
  if (axis === 'x') m.rotation.z = Math.PI / 2;
  if (axis === 'z') m.rotation.x = Math.PI / 2;
  m.castShadow = m.receiveShadow = true; parent.add(m); return m;
}

// ---------- nhà kho ----------
const floor = new THREE.Mesh(new THREE.PlaneGeometry(120, 80), M(0xb9bec2, { roughness: 0.95 }));
floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
const lineMat = M(0xf2c230);
for (const z of [-1.9, 1.9]) box(40, 0.01, 0.1, lineMat, 6, 0.006, z);
for (let x = -8; x <= 22; x += 10) { box(0.5, 9, 0.5, M(0x6f8596), x, 4.5, -8); }

// ---------- xe container bạt ----------
const BED_L = 12.26, BED_W = 2.35, BED_Y = 1.2, WALL = 0.8, ROOF = 2.15;
const truck = new THREE.Group(); scene.add(truck);
const steel = M(0x8c969e, { metalness: 0.4, roughness: 0.5 });
box(BED_L, 0.12, BED_W, M(0x6b5a4a), BED_L / 2, BED_Y - 0.06, 0, truck);                // sàn thùng
box(BED_L + 0.3, 0.3, 1.0, M(0x2b2f33), BED_L / 2 - 0.3, BED_Y - 0.3, 0, truck);         // khung gầm
for (const z of [-1, 1]) box(BED_L, WALL, 0.05, steel, BED_L / 2, BED_Y + WALL / 2, z * BED_W / 2, truck); // thành
box(0.06, ROOF, BED_W, steel, 0.03, BED_Y + ROOF / 2, 0, truck);                           // vách đầu
box(0.06, WALL, BED_W, steel, BED_L - 0.03, BED_Y + WALL / 2, 0, truck);                   // cửa sau (phần thành)
for (let x = 0; x <= BED_L + 0.01; x += BED_L / 6) for (const z of [-1, 1])
  box(0.08, ROOF, 0.08, steel, Math.min(x, BED_L - 0.04), BED_Y + ROOF / 2, z * (BED_W / 2 + 0.02), truck); // cột mui
const cab = new THREE.Group(); truck.add(cab); cab.position.set(-1.35, 0, 0);
box(2.3, 2.3, 2.45, M(0x2f6db3, { roughness: 0.4 }), 0, 1.95, 0, cab);
box(0.05, 0.9, 2.1, M(0x1c2a35, { roughness: 0.1, metalness: 0.6 }), -1.16, 2.5, 0, cab); // kính
box(2.3, 0.35, 2.45, M(0xe6e6e6), 0, 0.95, 0, cab);
const wheelMat = M(0x1b1b1b, { roughness: 0.9 });
for (const x of [-1.3, 7.6, 8.9, 10.2]) for (const z of [-1, 1]) {
  const w = cyl(0.5, 0.35, wheelMat, truck, 'z'); w.position.set(x, 0.5, z * 1.05);
}
// bạt (mái + 2 bên phía trên thành) - trượt về phía cabin khi mở
const tarp = new THREE.Group(); truck.add(tarp);
const tarpMat = M(0x2d5d8a, { roughness: 0.85, side: THREE.DoubleSide });
const tRoof = box(BED_L, 0.04, BED_W + 0.1, tarpMat, BED_L / 2, BED_Y + ROOF, 0, tarp);
const tSide = [-1, 1].map(z => box(BED_L, ROOF - WALL, 0.03, tarpMat, BED_L / 2, BED_Y + WALL + (ROOF - WALL) / 2, z * (BED_W / 2 + 0.06), tarp));
const tBack = box(0.03, ROOF - WALL, BED_W + 0.1, tarpMat, BED_L, BED_Y + WALL + (ROOF - WALL) / 2, 0, tarp);
function setTarp(open) { // 0 đóng, 1 mở (gom về đầu thùng)
  const s = 1 - 0.93 * open;
  tarp.scale.x = s; tarp.position.x = 0;
}

// ---------- bao đường 50 kg (75 x 50 x 13 cm) ----------
function bagTexture() {
  const c = document.createElement('canvas'); c.width = 256; c.height = 170;
  const g = c.getContext('2d'); g.fillStyle = '#f4f1e8'; g.fillRect(0, 0, 256, 170);
  g.strokeStyle = 'rgba(0,0,0,0.05)';
  for (let i = 0; i < 256; i += 4) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 170); g.stroke(); }
  g.fillStyle = '#2f6db3'; g.fillRect(0, 22, 256, 10); g.fillRect(0, 138, 256, 10);
  g.font = 'bold 44px DejaVu Sans'; g.textAlign = 'center'; g.fillText('KCP', 128, 100);
  g.font = 'bold 20px DejaVu Sans'; g.fillStyle = '#c0392b'; g.fillText('ĐƯỜNG · 50 KG', 128, 126);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const BL = 0.75, BWD = 0.5, BH = 0.13;
const bagGeo = new RoundedBoxGeometry(BL, BH, BWD, 3, 0.05);
const plain = M(0xece7da, { roughness: 0.95 });
const bagMat = new THREE.MeshStandardMaterial({ map: bagTexture(), roughness: 0.95 });
function newBag() { const m = new THREE.Mesh(bagGeo, bagMat); m.castShadow = m.receiveShadow = true; scene.add(m); return m; }

// sơ đồ xếp: mỗi đoạn dài 0,5 m dọc xe; 3 bao nằm ngang thùng (dài 75 cm theo bề ngang); 8 lớp
const SECT = 23, COLS = 3, LAY = 8;
const slots = [];
for (let s = 0; s < SECT; s++) for (let l = 0; l < LAY; l++) for (let c = 0; c < COLS; c++)
  slots.push({ s, x: 0.2 + 0.5 * s + 0.25, y: BED_Y + BH / 2 + l * BH, z: (c - 1) * 0.76 });
// đặt bao phía xa trước, gần sau
slots.sort((a, b) => a.s - b.s || (a.y - b.y) || (a.z - b.z));
const N = slots.length;
const placed = slots.map(() => { const b = newBag(); b.visible = false; b.rotation.y = Math.PI / 2; return b; });

// ---------- ray, băng tải ----------
const RZ = 3.0, CZ = 4.45, CY = 1.0;
for (const dz of [-0.35, 0.35]) box(16, 0.12, 0.12, M(0x555b60, { metalness: 0.6 }), 5.5, 0.06, RZ + dz);
box(16, 0.08, 0.9, M(0x3a3f44), 5.5, 0.04, RZ);
const conv = new THREE.Group(); scene.add(conv);
box(16, 0.06, 0.8, M(0x26332b), 5.5, CY - 0.03, CZ, conv);
for (const dz of [-0.43, 0.43]) box(16, 0.18, 0.06, M(0x7b8288, { metalness: 0.5 }), 5.5, CY, CZ + dz, conv);
for (let x = -2.3; x <= 13.3; x += 1.3) for (const dz of [-0.4, 0.4]) box(0.08, CY, 0.08, steel, x, CY / 2, CZ + dz, conv);
const convBags = Array.from({ length: 16 }, () => newBag());

// ---------- robot xếp bao 4 trục (vàng) ----------
const yellow = M(0xf2b705, { roughness: 0.45, metalness: 0.2 });
const dark = M(0x2b2f33, { roughness: 0.6 });
const robot = new THREE.Group(); scene.add(robot);
box(1.3, 0.35, 1.1, dark, 0, 0.3, RZ, robot);                    // xe con chạy trên ray
const ped = cyl(0.42, 0.55, yellow, robot); ped.position.set(0, 0.75, RZ);
const turret = new THREE.Group(); turret.position.set(0, 1.02, RZ); robot.add(turret);
cyl(0.5, 0.25, dark, turret).position.set(0, 0.12, 0);
box(0.7, 0.5, 0.6, yellow, 0.05, 0.5, 0, turret);
const L1 = 2.1, L2 = 2.3, SH_A = 0.25, SH_Y = 0.6, G = 0.42;
const shoulder = new THREE.Group(); shoulder.position.set(SH_A, SH_Y, 0); turret.add(shoulder);
box(L1, 0.28, 0.3, yellow, L1 / 2, 0, 0, shoulder);
cyl(0.2, 0.42, dark, shoulder, 'z');
const elbow = new THREE.Group(); elbow.position.set(L1, 0, 0); shoulder.add(elbow);
cyl(0.17, 0.4, dark, elbow, 'z');
box(L2, 0.2, 0.22, yellow, L2 / 2, 0, 0, elbow);
const wrist = new THREE.Group(); wrist.position.set(L2, 0, 0); elbow.add(wrist);
const grip = new THREE.Group(); wrist.add(grip);
cyl(0.07, G - 0.08, dark, grip).position.set(0, -(G - 0.08) / 2, 0);
box(0.5, 0.06, 0.34, M(0x9aa3aa, { metalness: 0.6 }), 0, -G + 0.06, 0, grip);    // tấm đầu gắp
const fingers = [];
for (const s of [-1, 1]) for (const k of [-0.2, 0, 0.2]) {
  const f = box(0.05, 0.28, 0.05, dark, k, -G - 0.06, s * 0.3, grip); f.userData.s = s; fingers.push(f);
}
// máy quét LiDAR trên cột phía đầu xe
const lidarPos = new THREE.Vector3(-1.2, 5.2, RZ - 0.3);
box(0.15, 5.2, 0.15, steel, lidarPos.x, 2.6, lidarPos.z);
const lidarHead = box(0.45, 0.3, 0.45, M(0x1d2b3a), lidarPos.x, lidarPos.y, lidarPos.z);
const glow = new THREE.MeshBasicMaterial({ color: 0x28d17c, transparent: true, opacity: 0.25, side: THREE.DoubleSide, depthWrite: false });
const scanPlane = new THREE.Mesh(new THREE.PlaneGeometry(BED_W + 0.2, ROOF + 0.1), glow);
scanPlane.rotation.y = Math.PI / 2; scene.add(scanPlane);
const beamGeo = new THREE.BufferGeometry(); beamGeo.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(24), 3));
const beams = new THREE.LineSegments(beamGeo, new THREE.LineBasicMaterial({ color: 0x28d17c, transparent: true }));
scene.add(beams);
const outline = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(BED_L, ROOF, BED_W)),
  new THREE.LineBasicMaterial({ color: 0x28d17c, transparent: true }));
outline.position.set(BED_L / 2, BED_Y + ROOF / 2, 0); scene.add(outline);

// ---------- tiện ích thời gian ----------
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const ss = x => { x = clamp(x); return x * x * (3 - 2 * x); };
const seg = (t, a, b) => ss((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const V = (x, y, z) => new THREE.Vector3(x, y, z);

// lịch đặt bao: T[k] = lúc bao k nằm xuống thùng
const T = [];
const SLOW = [[12, 17], [17, 22]];           // 2 bao đầu chậm
for (let k = 0; k < N; k++) {
  if (k < 2) T.push(SLOW[k][1]);
  else if (k < 10) T.push(22 + (k - 1) * 1.25);
  else T.push(32 + (k - 9) * (12 / (N - 9)));
}
const cycStart = k => (k === 0 ? 12 : T[k - 1]);
const HOME_X = -0.4;
const PICK_DX = 0.0;                         // điểm gắp trên băng tải, ngay cạnh robot
const SAFE = 3.15;

function bagIdxAt(t) { let k = 0; while (k < N - 1 && T[k] <= t) k++; return k; }
function carriageX(t) {
  if (t < 12) return HOME_X;
  if (t < 44) {
    const k = bagIdxAt(t); const s = slots[k].x;
    if (t < 13.5) return lerp(HOME_X, slots[0].x, seg(t, 12, 13.5));
    if (t < 32) return slots[0].x;
    // tua nhanh: chạy theo đoạn đang xếp (làm mượt)
    const kf = k - 1 + clamp((t - T[k - 1]) / (T[k] - T[k - 1]));
    return slots[0].x + 0.5 * Math.min(kf, N - 1) / (COLS * LAY);
  }
  return lerp(slots[N - 1].x, HOME_X, seg(t, 44, 47.5));
}

// tư thế đầu gắp (tâm bao) và góc xoay bao theo pha chu kỳ
function cyclePose(k, u, rx) {
  const sl = slots[k];
  const P = V(rx + PICK_DX, CY + BH / 2 + 0.02, CZ);
  const Hp = V(P.x, SAFE, P.z);
  const Tg = V(sl.x, sl.y, sl.z);
  const Ht = V(sl.x, SAFE + 0.2, sl.z);
  const prev = k > 0 ? slots[k - 1] : null;
  const L0 = prev ? V(prev.x, SAFE, prev.z) : V(rx + 1.2, SAFE, RZ - 1.2);
  const keys = [[0, L0, 0], [0.2, Hp, 0], [0.3, P, 0], [0.36, P, 0], [0.46, Hp, 0], [0.7, Ht, 1], [0.84, Tg, 1], [0.9, Tg, 1], [1, V(sl.x, SAFE, sl.z), 1]];
  let i = 0; while (i < keys.length - 2 && u > keys[i + 1][0]) i++;
  const [u0, a, ra] = keys[i], [u1, b, rb] = keys[i + 1];
  const e = ss((u - u0) / (u1 - u0));
  return { pos: a.clone().lerp(b, e), rot: lerp(ra, rb, e), hold: u >= 0.33 && u < 0.87, close: u >= 0.3 && u < 0.88 ? 1 : 0 };
}

function solveArm(rx, target, bagYaw, close) {
  robot.position.x = rx;
  const base = V(rx, 1.02, RZ);
  const wristP = target.clone().add(V(0, BH / 2 + G + 0.06, 0));
  const dx = wristP.x - base.x, dz = wristP.z - base.z;
  const yaw = Math.atan2(-dz, dx);
  turret.rotation.y = yaw;
  const r = Math.hypot(dx, dz) - SH_A, h = wristP.y - (base.y + SH_Y);
  let d = Math.hypot(r, h); d = clamp(d, Math.abs(L1 - L2) + 0.05, L1 + L2 - 0.02);
  const ce = clamp((d * d - L1 * L1 - L2 * L2) / (2 * L1 * L2), -1, 1);
  const e = Math.acos(ce);
  const p1 = Math.atan2(h, r) + Math.atan2(L2 * Math.sin(e), L1 + L2 * Math.cos(e));
  const p2 = p1 - e;
  shoulder.rotation.z = p1; elbow.rotation.z = p2 - p1; wrist.rotation.z = -p2;
  grip.rotation.y = bagYaw - yaw;
  for (const f of fingers) f.position.z = f.userData.s * lerp(0.36, 0.27, close);
}

// ---------- camera ----------
const CAMS = [
  [0, V(24, 10, 19), V(6, 1.5, 0)], [5, V(17, 8, 16), V(5, 1.6, 0)],
  [5.8, V(10, 10.5, 14), V(5, 2, 0.5)], [12, V(6, 11, 12.5), V(5, 2, 0.5)],
  [13, V(3.6, 5.0, 9.6), V(0.6, 1.9, 2.0)], [22, V(3.0, 5.4, 9.0), V(0.6, 1.9, 1.8)],
  [23, V(5.2, 8.6, 6.4), V(1.0, 1.4, 0.2)], [32, V(4.6, 9.2, 5.8), V(1.0, 1.4, 0.0)],
];
function camAt(t) {
  if (t >= 32.6 && t < 44.6) { // bám theo robot khi tua nhanh
    const rx = carriageX(t);
    return [V(rx + 5.0, 8.0, 9.5), V(rx - 0.5, 1.6, 0.3)];
  }
  if (t >= 44.6) {
    const a = [V(18, 10, 18), V(5.5, 1.6, 0)], b = [V(15, 8, 16), V(5.5, 1.6, 0)];
    const k = seg(t, 44.6, 52);
    return [a[0].clone().lerp(b[0], k), a[1].clone().lerp(b[1], k)];
  }
  let i = 0; while (i < CAMS.length - 2 && t > CAMS[i + 1][0]) i++;
  const [t0, p0, l0] = CAMS[i], [t1, p1, l1] = CAMS[i + 1];
  const k = seg(t, t0, t1);
  return [p0.clone().lerp(p1, k), l0.clone().lerp(l1, k)];
}
// trộn camera mượt ở 2 mốc chuyển sang/ra khỏi chế độ bám
function camera_(t) {
  const blend = (ta, tb) => { const a = camAt(ta - 0.001), b = camAt(t); const k = seg(t, ta, tb);
    return [a[0].clone().lerp(b[0], k), a[1].clone().lerp(b[1], k)]; };
  if (t >= 32.6 && t < 33.8) return blend(32.6, 33.8);
  if (t >= 44.6 && t < 46) return blend(44.6, 46);
  return camAt(t);
}

// ---------- nhãn ----------
const STEPS = [[0, 5, 1, 'Xe vào vị trí'], [5, 12, 2, 'Mở bạt · quét LiDAR thùng xe'], [12, 22, 3, 'Gắp bao từ băng tải'],
  [22, 32, 4, 'Xếp bao từ đầu thùng'], [32, 44, 5, 'Xếp dần ra cửa sau'], [44, 52, 6, 'Xe đầy · đóng bạt']];
const stepEl = document.getElementById('step'), ffEl = document.getElementById('ff');

// ---------- dựng khung tại thời điểm t ----------
window.renderAt = function (t) {
  // xe chạy vào
  truck.position.x = lerp(24, 0, ss(clamp(t / 4.6)));
  setTarp(t < 44 ? seg(t, 5, 7.5) : 1 - seg(t, 47.5, 51));

  // LiDAR
  const sw = seg(t, 7.5, 10.8);
  const scanOn = t > 7.4 && t < 11;
  scanPlane.visible = beams.visible = scanOn;
  if (scanOn) {
    const x = lerp(0.1, BED_L - 0.1, sw);
    scanPlane.position.set(x, BED_Y + ROOF / 2, 0);
    const cs = [[-1, -1], [-1, 1], [1, 1], [1, -1]].map(([a, b]) => V(x, BED_Y + (b > 0 ? ROOF : 0), a * BED_W / 2));
    const arr = beamGeo.attributes.position.array; let j = 0;
    for (const c of cs) { arr.set([lidarPos.x, lidarPos.y, lidarPos.z, c.x, c.y, c.z], j); j += 6; }
    beamGeo.attributes.position.needsUpdate = true;
  }
  outline.visible = t > 10.6 && t < 13;
  outline.material.opacity = Math.min(seg(t, 10.6, 11.2), 1 - seg(t, 12.3, 13)) * (0.6 + 0.4 * Math.sin(t * 12));
  lidarHead.rotation.y = t * 3;

  // robot + bao
  const rx = carriageX(t);
  let pose, holdIdx = -1;
  if (t < 12 || t >= 44) {
    const restT = V(rx + 1.6, 2.6, RZ - 1.4);
    if (t >= 44) {
      const last = slots[N - 1];
      const from = V(last.x, SAFE, last.z);
      pose = { pos: from.lerp(restT, seg(t, 44, 46)), rot: 1, close: 0 };
    } else pose = { pos: restT, rot: 0, close: 0 };
  } else if (t < 32) {
    const k = bagIdxAt(t); const u = clamp((t - cycStart(k)) / (T[k] - cycStart(k)));
    pose = cyclePose(k, u, rx); if (pose.hold) holdIdx = k;
  } else {
    // tua nhanh: động tác gắp - đặt lặp lại nhanh, bao xuất hiện theo lịch
    const k = bagIdxAt(t); const u = ((t - 32) * 1.6) % 1;
    pose = cyclePose(k, 0.2 + u * 0.7, rx);
  }
  solveArm(rx, pose.pos, pose.rot * Math.PI / 2, pose.close);

  for (let k = 0; k < N; k++) {
    const b = placed[k], sl = slots[k];
    if (k === holdIdx) {
      b.visible = true; b.position.copy(pose.pos);
      b.rotation.set(0, pose.rot * Math.PI / 2, 0);
    } else if (t >= T[k]) {
      b.visible = true; const drop = t >= 32 && t < 44 ? (1 - seg(t, T[k], T[k] + 0.12)) * 0.25 : 0;
      b.position.set(sl.x, sl.y + drop, sl.z); b.rotation.set(0, Math.PI / 2, 0);
    } else b.visible = false;
  }

  // băng tải: hàng bao chờ chạy về điểm gắp
  const pickX = rx + PICK_DX, sp = 1.0;
  let shift = 0, headOn = true;
  if (t >= 12 && t < 32) { const k = bagIdxAt(t); const u = clamp((t - cycStart(k)) / (T[k] - cycStart(k)));
    shift = seg(u, 0.36, 0.7); headOn = u < 0.33; }
  else if (t >= 32 && t < 44) shift = ((t - 32) * 3) % 1;
  convBags.forEach((b, j) => {
    const x = pickX + sp * (j - shift);
    b.position.set(x, CY + BH / 2 + 0.02, CZ); b.rotation.set(0, 0, 0);
    b.visible = x <= 13.4 && x >= pickX - 0.01 && (j > 0 || headOn);
  });

  // nhãn
  const st = STEPS.find(s => t >= s[0] && t < s[1]) || STEPS[STEPS.length - 1];
  stepEl.innerHTML = `<b>${st[2]}</b>${st[3]}`;
  stepEl.style.opacity = Math.min(seg(t, st[0], st[0] + 0.4), st[2] === 6 ? 1 : 1 - seg(t, st[1] - 0.25, st[1]));
  ffEl.style.opacity = t >= 32.3 && t < 44 ? 1 : 0;

  const [cp, cl] = camera_(t);
  camera.position.copy(cp); camera.lookAt(cl);
  renderer.render(scene, camera);
  return true;
};
window.DUR = DUR;
window.ready = true;
