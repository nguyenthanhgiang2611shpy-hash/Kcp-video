// Minh họa 3D máy DEPAL bao tự động – KCP Phú Yên.
// Mặt bằng lấy theo bản vẽ LA26-PTC-KCP-DEP-301026 (20/10/2026); vận hành theo Phon-Tech xác nhận 04/11/2026.
// Đơn vị mét. x: ngang bản vẽ (trái -> phải), z: dọc bản vẽ (trên -> dưới), y: lên.
// Cao độ từng băng tải, chiều cao sàn xe, vị trí phòng điều khiển: MINH HỌA (bản vẽ không có số);
// chỉ biết điểm cao nhất hệ thống băng tải = 1,5 m.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const W = 1280, H = 720;
const CLEAN = new URLSearchParams(location.search).get('clean') === '1';   // bỏ chữ phủ (để ghép chia đôi màn hình)
if (CLEAN) document.querySelectorAll('.corner, #foot').forEach(e => e.style.display = 'none');
const SCN = [['overview', 14], ['area', 11], ['flow', 27], ['pick', 20], ['journey', 14],
             ['truck', 24], ['sensor', 21], ['backup', 12], ['summary', 12]];
const SC = {}; let acc = 0;
for (const [n, d] of SCN) { SC[n] = [acc, d]; acc += d; }
const DUR = acc;

// ---------- tiện ích ----------
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const ss = x => { x = clamp(x); return x * x * (3 - 2 * x); };
const seg = (t, a, b) => ss((t - a) / (b - a));
const lin = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const MMPX = 13258 / (910 - 337);
const X = px => (px - 337) * MMPX / 1000, Z = py => (py - 323) * MMPX / 1000;
function kx(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++)
    if (t < keys[i + 1][0]) return lerp(keys[i][1], keys[i + 1][1], seg(t, keys[i][0], keys[i + 1][0]));
  return keys[keys.length - 1][1];
}

// ---------- renderer ----------
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H); renderer.setPixelRatio(1);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.prepend(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xe4e6e3);
scene.fog = new THREE.Fog(0xe4e6e3, 55, 110);
const camera = new THREE.PerspectiveCamera(40, W / H, 0.1, 300);
scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8f94, 1.45));
const sun = new THREE.DirectionalLight(0xffffff, 2.1);
sun.position.set(2, 26, 26); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -22, right: 22, top: 22, bottom: -22, near: 1, far: 80 });
sun.shadow.bias = -0.0005; scene.add(sun); scene.add(sun.target); sun.target.position.set(15, 0, 9);

const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.7, metalness: 0.1, ...o });
function box(w, h, d, mat, x = 0, y = 0, z = 0, parent = scene, shadow = true) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z); m.castShadow = shadow; m.receiveShadow = true; parent.add(m); return m;
}
const unitCyl = new THREE.CylinderGeometry(1, 1, 1, 16);
function rod(r, mat, parent = scene) {
  const m = new THREE.Mesh(unitCyl, mat); m.userData.r = r; m.castShadow = true; parent.add(m); return m;
}
const UP = V(0, 1, 0);
function setRod(m, a, b) {
  const d = b.clone().sub(a), L = d.length();
  m.position.copy(a).add(b).multiplyScalar(0.5);
  m.quaternion.setFromUnitVectors(UP, d.normalize());
  m.scale.set(m.userData.r, Math.max(L, 1e-3), m.userData.r);
}
function cylAt(r, h, mat, x, y, z, axis = 'y', parent = scene) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 20), mat);
  if (axis === 'x') m.rotation.z = Math.PI / 2; if (axis === 'z') m.rotation.x = Math.PI / 2;
  m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; parent.add(m); return m;
}
function canvasTex(w, h, draw, rep) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  if (rep) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep[0], rep[1]); }
  t.anisotropy = 4; return t;
}

// ---------- màu thiết bị (giống video 2D) ----------
const COL = { L: 0x2c5fa0, R: 0x764a96, C: 0xb04030, V: 0x606814, S: 0x267a40, K: 0xb0800a, T: 0x107c80, X: 0x1d2b3a, M: 0xa0306c };
const CSS = k => '#' + COL[k].toString(16).padStart(6, '0');
const steel = M(0x8c969e, { metalness: 0.45, roughness: 0.45 });
const dark = M(0x2b2f33, { roughness: 0.6 });

// ---------- sàn kho (ô lưới 1 m) ----------
const floorTex = canvasTex(512, 512, (g, w, h) => {
  g.fillStyle = '#c3c7c8'; g.fillRect(0, 0, w, h); g.strokeStyle = 'rgba(60,70,75,0.16)'; g.lineWidth = 2;
  for (let i = 0; i <= 8; i++) { g.beginPath(); g.moveTo(i * 64, 0); g.lineTo(i * 64, h); g.stroke(); g.beginPath(); g.moveTo(0, i * 64); g.lineTo(w, i * 64); g.stroke(); }
}, [12.5, 10]);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(100, 80), new THREE.MeshStandardMaterial({ map: floorTex, roughness: 0.95 }));
floor.rotation.x = -Math.PI / 2; floor.position.set(16, 0, 10); floor.receiveShadow = true; scene.add(floor);
for (let x = -10; x <= 40; x += 10) box(0.5, 7, 0.5, M(0x8796a2), x, 3.5, -14);

// ---------- cao độ (minh họa) ----------
const RH = 0.45;            // mặt băng con lăn sling
const BY = 0.9;             // mặt băng nhận bao, vệ sinh
const TOP = 1.5;            // điểm cao nhất hệ thống băng tải (Phon-Tech)
const BH = 0.13, BAG_L = 0.75, BAG_W = 0.5;
const BED = 1.3;            // sàn thùng xe (minh họa – KCP còn kiểm tra)

// ---------- vị trí theo bản vẽ ----------
const CZ = Z(847.5);
const POS = { L0: X(375), L1: X(455), L2: X(536), C: X(627.5), R2: X(723), R1: X(792), R0: X(875) };
const BX = X(628);                                  // trục băng tải bao
const ROBOT_B = V(X(628), 0, Z(768));
const DROP_Z = Z(708);
const CURVE_C = V(X(683), TOP, Z(400)), CURVE_R = 55 * MMPX / 1000;
const TELE_Z = Z(345), TELE_X0 = X(683), TELE_X1 = X(1100);
const TRUCK_X0 = X(1132), TL = 12.26, TW = 2.35, FW = TRUCK_X0 + TL - 0.05;   // vách đầu thùng (trong)
const ST_C = V(X(629), 0, Z(1115));

// ---------- băng con lăn sling ----------
function rollerConv(x0, x1, z0, z1, col) {
  const g = new THREE.Group(); scene.add(g);
  const frame = M(col, { roughness: 0.5, metalness: 0.3 });
  for (const z of [z0, z1]) box(x1 - x0, 0.14, 0.08, frame, (x0 + x1) / 2, RH - 0.07, z, g);
  for (let x = x0 + 0.1; x <= x1; x += 1.0) for (const z of [z0, z1]) box(0.08, RH - 0.1, 0.08, dark, x, (RH - 0.1) / 2, z, g);
  const n = Math.floor((x1 - x0) / 0.16);
  const rm = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.035, 0.035, z1 - z0 - 0.1, 10), M(0xb9c0c5, { metalness: 0.6, roughness: 0.35 }), n);
  const q = new THREE.Quaternion().setFromAxisAngle(V(1, 0, 0), Math.PI / 2), m4 = new THREE.Matrix4();
  for (let i = 0; i < n; i++) { m4.compose(V(x0 + 0.08 + i * 0.16, RH - 0.035, (z0 + z1) / 2), q, V(1, 1, 1)); rm.setMatrixAt(i, m4); }
  rm.castShadow = rm.receiveShadow = true; g.add(rm); return g;
}
rollerConv(X(340), X(568), Z(800), Z(895), COL.L);
rollerConv(X(690), X(910), Z(800), Z(895), COL.R);
// đoạn con lăn trong cell (vị trí hút)
rollerConv(X(568) + 0.02, X(690) - 0.02, Z(800), Z(895), 0x8a5a50);

// sàn lưới cho công nhân (ô gạch chéo trên bản vẽ – Phon-Tech xác nhận)
const gridTex = canvasTex(128, 128, (g, w, h) => {
  g.fillStyle = '#8fb9bf'; g.fillRect(0, 0, w, h); g.strokeStyle = '#4f7d84'; g.lineWidth = 3;
  for (let i = -w; i < w * 2; i += 16) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i + h, h); g.stroke(); g.beginPath(); g.moveTo(i, h); g.lineTo(i + h, 0); g.stroke(); }
}, [8, 1]);
for (const [x0, x1] of [[X(350), X(500)], [X(752), X(905)]]) for (const [z0, z1] of [[Z(770), Z(792)], [Z(904), Z(926)]])
  box(x1 - x0, 0.12, z1 - z0, new THREE.MeshStandardMaterial({ map: gridTex, roughness: 0.8 }), (x0 + x1) / 2, 0.06, (z0 + z1) / 2);

// ---------- cell robot: khung + hàng rào ----------
const cellMat = M(COL.C, { roughness: 0.5, metalness: 0.3 });
const cx0 = X(570), cx1 = X(690), cz0 = Z(720), cz1 = Z(912);
for (const x of [cx0, cx1]) for (const z of [cz0, cz1]) box(0.14, 2.6, 0.14, cellMat, x, 1.3, z);
for (const z of [cz0, cz1]) box(cx1 - cx0, 0.12, 0.12, cellMat, (cx0 + cx1) / 2, 2.6, z);
for (const x of [cx0, cx1]) box(0.12, 0.12, cz1 - cz0, cellMat, x, 2.6, (cz0 + cz1) / 2);
const fenceMat = new THREE.MeshStandardMaterial({ color: 0xe0a040, transparent: true, opacity: 0.16, depthWrite: false, roughness: 0.6, side: THREE.DoubleSide });
const fencePx = [[500, 770], [556, 770], [556, 715], [700, 715], [700, 770], [748, 770]];
for (let i = 0; i < fencePx.length - 1; i++) {
  const a = V(X(fencePx[i][0]), 0, Z(fencePx[i][1])), b = V(X(fencePx[i + 1][0]), 0, Z(fencePx[i + 1][1]));
  const L = a.distanceTo(b), m = box(Math.abs(b.x - a.x) + 0.03, 1.8, Math.abs(b.z - a.z) + 0.03, fenceMat, (a.x + b.x) / 2, 0.9, (a.z + b.z) / 2, scene, false);
}

// ---------- băng nhận bao, băng vệ sinh, băng thẳng, băng cong ----------
function beltZ(x, z0, z1, y0, y1, w, col, legs = true) {     // băng chạy theo z, cao y0 -> y1
  const g = new THREE.Group(); scene.add(g);
  const L = Math.hypot(z1 - z0, y1 - y0), ang = Math.atan2(y1 - y0, z1 - z0);
  const body = box(w, 0.08, L, M(0x3a3f44, { roughness: 0.85 }), 0, 0, 0, g);
  const rail = M(col, { roughness: 0.5, metalness: 0.3 });
  for (const dx of [-w / 2 - 0.04, w / 2 + 0.04]) box(0.06, 0.16, L, rail, dx, 0.03, 0, g);
  g.position.set(x, (y0 + y1) / 2 - 0.04, (z0 + z1) / 2); g.rotation.x = -ang;
  if (legs) for (let k = 0.1; k <= 0.95; k += 0.28) {
    const z = lerp(z0, z1, k), y = lerp(y0, y1, k);
    for (const dx of [-w / 2, w / 2]) box(0.06, y - 0.08, 0.06, dark, x + dx, (y - 0.08) / 2, z);
  }
  return g;
}
beltZ(BX, Z(735), Z(660), BY, BY, 0.7, 0x8c969e);                          // đoạn nhận bao trong cell
beltZ(BX, Z(660), Z(597), BY, BY, 0.7, COL.V);                             // băng vệ sinh
beltZ(BX, Z(597), Z(400), BY, TOP, 0.7, COL.S);                            // băng thẳng (lên 1,5 m)
// 4 tay xám ở cửa cell (bản vẽ không ghi tên)
for (const dx of [-0.55, 0.55]) for (const z of [Z(684), Z(712)]) {
  cylAt(0.06, 0.5, M(0x9aa0a4), BX + dx, BY - 0.1, z);
  box(0.3, 0.05, 0.05, M(0x9aa0a4), BX + dx * 0.75, BY + 0.12, z);
}
// vỏ băng vệ sinh + 3 chổi quét
const vg = new THREE.Group(); scene.add(vg);
const vMat = new THREE.MeshStandardMaterial({ color: COL.V, transparent: true, opacity: 0.35, roughness: 0.6, side: THREE.DoubleSide });
const vz0 = Z(660), vz1 = Z(597);
for (const dx of [-0.48, 0.48]) box(0.03, 0.6, vz0 - vz1, vMat, BX + dx, BY + 0.3, (vz0 + vz1) / 2, vg, false);
box(1.0, 0.03, vz0 - vz1, vMat, BX, BY + 0.6, (vz0 + vz1) / 2, vg, false);
const brushTex = canvasTex(128, 64, (g, w, h) => {
  g.fillStyle = '#3b3320'; g.fillRect(0, 0, w, h); g.strokeStyle = '#c9b36a'; g.lineWidth = 2;
  for (let i = 0; i < w; i += 5) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i + 3, h); g.stroke(); }
}, [1, 3]);
const brushes = [];
for (let i = 0; i < 3; i++) brushes.push(cylAt(0.12, 0.66, new THREE.MeshStandardMaterial({ map: brushTex, roughness: 1 }), BX, BY + 0.13 + 0.13, lerp(vz0, vz1, 0.2 + 0.3 * i), 'x', vg));
// băng cong 90° ở cao độ 1,5 m
const curve = new THREE.Mesh(new THREE.RingGeometry(CURVE_R - 0.35, CURVE_R + 0.35, 40, 1, Math.PI / 2, Math.PI / 2), M(0x3a3f44, { side: THREE.DoubleSide }));
curve.rotation.x = -Math.PI / 2; curve.position.set(CURVE_C.x, TOP, CURVE_C.z); curve.receiveShadow = true; scene.add(curve);
for (const r of [CURVE_R - 0.39, CURVE_R + 0.39]) {
  const tor = new THREE.Mesh(new THREE.TorusGeometry(r, 0.04, 8, 40, Math.PI / 2), M(COL.K, { metalness: 0.3 }));
  tor.rotation.x = -Math.PI / 2; tor.rotation.z = Math.PI / 2; tor.position.set(CURVE_C.x, TOP + 0.03, CURVE_C.z); scene.add(tor);
}
for (const a of [200, 235, 260]) { const r = a * Math.PI / 180; box(0.06, TOP - 0.05, 0.06, dark, CURVE_C.x + CURVE_R * Math.cos(r), (TOP - 0.05) / 2, CURVE_C.z + CURVE_R * Math.sin(r)); }

// ---------- băng tải ống lồng ----------
const teleMat = M(COL.T, { roughness: 0.45, metalness: 0.3 });
box(TELE_X1 - TELE_X0, 0.45, 1.0, teleMat, (TELE_X0 + TELE_X1) / 2, TOP - 0.25, TELE_Z);
box(TELE_X1 - TELE_X0, 0.02, 0.7, M(0x3a3f44), (TELE_X0 + TELE_X1) / 2, TOP + 0.0, TELE_Z);
for (let x = TELE_X0 + 0.4; x < TELE_X1; x += 2.2) for (const dz of [-0.4, 0.4]) box(0.08, TOP - 0.45, 0.08, dark, x, (TOP - 0.45) / 2, TELE_Z + dz);
const teleSec = [0.92, 0.84, 0.76].map((w, i) => box(1, 0.36 - i * 0.04, w, M([0x13878b, 0x1a9599, 0x22a3a6][i], { roughness: 0.4, metalness: 0.3 }), 0, TOP - 0.2, TELE_Z));
const headG = new THREE.Group(); scene.add(headG);
box(0.55, 0.32, 0.62, M(0x0d6a6d, { metalness: 0.3 }), 0, 0, 0, headG);
box(0.12, 0.08, 0.12, M(0x111111), 0.3, 0.12, -0.2, headG);             // cảm biến
box(0.12, 0.08, 0.12, M(0x111111), 0.3, 0.12, 0.2, headG);
const headArm = rod(0.07, M(0x0d6a6d, { metalness: 0.3 }));
function setTele(endX, head) {        // endX: mút băng ống lồng; head: vị trí đầu rải (Vector3) hoặc null
  const a = TELE_X1 - 0.3, L = Math.max(endX - a, 0.3);
  const cuts = [[0, 0.4], [0.37, 0.72], [0.69, 1.0]];
  teleSec.forEach((m, i) => { const x0 = a + L * cuts[i][0], x1 = a + L * cuts[i][1]; m.position.x = (x0 + x1) / 2; m.scale.x = Math.max(x1 - x0, 0.05); });
  const hp = head || V(endX + 0.4, TOP, TELE_Z);
  headG.position.copy(hp);
  setRod(headArm, V(endX, TOP - 0.05, TELE_Z), hp);
}

// ---------- xe container bạt 34T (đã bỏ bạt để nhìn vào trong) ----------
const tg = new THREE.Group(); scene.add(tg);
box(TL, 0.12, TW, M(0x6b5a4a), TRUCK_X0 + TL / 2, BED - 0.06, TELE_Z, tg);
box(TL + 1.2, 0.35, 1.0, dark, TRUCK_X0 + TL / 2 + 0.6, BED - 0.32, TELE_Z, tg);
for (const dz of [-1, 1]) box(TL, 0.8, 0.05, steel, TRUCK_X0 + TL / 2, BED + 0.4, TELE_Z + dz * TW / 2, tg);
box(0.06, 2.15, TW, steel, TRUCK_X0 + TL - 0.03, BED + 1.075, TELE_Z, tg);
for (let i = 0; i <= 6; i++) for (const dz of [-1, 1]) box(0.08, 2.15, 0.08, steel, TRUCK_X0 + Math.min(i * TL / 6, TL - 0.04), BED + 1.075, TELE_Z + dz * (TW / 2 + 0.02), tg);
for (const dz of [-1, 1]) box(TL, 0.06, 0.06, steel, TRUCK_X0 + TL / 2, BED + 2.15, TELE_Z + dz * (TW / 2 + 0.02), tg);
const cab = new THREE.Group(); tg.add(cab); cab.position.set(TRUCK_X0 + TL + 1.3, 0, TELE_Z);
box(2.3, 2.3, 2.45, M(0x2f6db3, { roughness: 0.4 }), 0, 1.95, 0, cab);
box(0.05, 0.9, 2.1, M(0x1c2a35, { roughness: 0.1, metalness: 0.6 }), 1.16, 2.5, 0, cab);
for (const x of [TRUCK_X0 + 1.5, TRUCK_X0 + 2.8, TRUCK_X0 + 4.1, TRUCK_X0 + TL + 1.3]) for (const dz of [-1, 1])
  cylAt(0.5, 0.35, M(0x1b1b1b, { roughness: 0.9 }), x, 0.5, TELE_Z + dz * 1.05, 'z', tg);
const limitPlane = new THREE.Mesh(new THREE.PlaneGeometry(TL, TW), new THREE.MeshBasicMaterial({ color: 0xd04030, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false }));
limitPlane.rotation.x = -Math.PI / 2; limitPlane.position.set(TRUCK_X0 + TL / 2, BED + 2.15 - 0.3, TELE_Z); scene.add(limitPlane);

// ---------- trạm xả tay dự phòng ----------
beltZ(BX, Z(1053), Z(912), BY, BY, 0.7, COL.M);
const stMat = M(COL.M, { roughness: 0.55, metalness: 0.2 });
const sx0 = X(562), sx1 = X(695), sz0 = Z(1053), sz1 = Z(1158);
for (const [a, b, c, d] of [[sx0, sz0, sx1, sz0], [sx0, sz1, sx1, sz1], [sx0, sz0, sx0, sz1], [sx1, sz0, sx1, sz1]])
  box(Math.abs(c - a) + 0.1, 0.1, Math.abs(d - b) + 0.1, stMat, (a + c) / 2, 0.05, (b + d) / 2);
box(2.4, 0.15, 1.6, M(0x7d7d7d), ST_C.x, 0.075, ST_C.z);

// ---------- phòng điều khiển (vị trí minh họa – chưa có trên bản vẽ) ----------
const CR = V(15.0, 0, 5.2);
const crg = new THREE.Group(); crg.position.copy(CR); scene.add(crg);
const wall = M(0xd9d4c7, { roughness: 0.9 });
box(3.2, 2.6, 0.1, wall, 0, 1.3, -1.4, crg); box(0.1, 2.6, 2.8, wall, -1.6, 1.3, 0, crg); box(0.1, 2.6, 2.8, wall, 1.6, 1.3, 0, crg);
box(3.3, 0.1, 2.9, wall, 0, 2.65, 0, crg);
box(2.2, 0.08, 0.7, M(0x6b5a4a), 0, 0.78, -0.9, crg);
for (const dx of [-1, 1]) box(0.06, 0.78, 0.6, dark, dx * 1.0, 0.39, -0.9, crg);
const monCanvas = document.createElement('canvas'); monCanvas.width = 512; monCanvas.height = 300;
const monTex = new THREE.CanvasTexture(monCanvas); monTex.colorSpace = THREE.SRGBColorSpace;
let monState = '';
function drawMonitor(state, blink) {
  const key = state + blink; if (key === monState) return; monState = key;
  const g = monCanvas.getContext('2d'); g.fillStyle = '#1e2832'; g.fillRect(0, 0, 512, 300);
  g.fillStyle = '#9fb3c2'; g.font = 'bold 26px DejaVu Sans Mono'; g.fillText('CẢM BIẾN', 24, 50);
  const rows = [['(A) THÙNG XE', 'ĐÚNG', '#5ad070'], ['(B) VỊ TRÍ BAO', state === 'bad' ? 'SAI' : 'ĐÚNG', state === 'bad' ? '#ff5a4a' : '#5ad070']];
  rows.forEach(([a, b, c], i) => {
    g.fillStyle = '#e6e6e6'; g.font = 'bold 32px DejaVu Sans Mono'; g.fillText(a, 24, 130 + i * 90);
    if (!(state === 'bad' && i === 1 && blink)) { g.fillStyle = c; g.font = 'bold 44px DejaVu Sans Mono'; g.textAlign = 'right'; g.fillText(b, 492, 132 + i * 90); g.textAlign = 'left'; }
  });
  monTex.needsUpdate = true;
}
drawMonitor('ok', false);
const mon = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 0.76), new THREE.MeshBasicMaterial({ map: monTex }));
mon.position.set(-0.5, 1.3, -1.15); crg.add(mon);
box(1.36, 0.82, 0.04, dark, -0.5, 1.3, -1.19, crg);
const stopBtn = cylAt(0.12, 0.1, M(0xd02a20, { emissive: 0x000000 }), 0.25, 0.87, -0.7, 'y', crg);
cylAt(0.17, 0.04, M(0xf2c230), 0.25, 0.83, -0.7, 'y', crg);

// ---------- người ----------
function makePerson(vest = 0xe8762a, hat = 0xf2c230) {
  const g = new THREE.Group(); scene.add(g);
  for (const dz of [-0.1, 0.1]) box(0.14, 0.8, 0.14, M(0x2c3a4a), 0, 0.4, dz, g);
  box(0.26, 0.6, 0.44, M(vest), 0, 1.1, 0, g);
  const armL = box(0.1, 0.55, 0.1, M(vest), 0, 1.1, -0.28, g), armR = box(0.1, 0.55, 0.1, M(vest), 0, 1.1, 0.28, g);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 12), M(0xd8a77e)); head.position.set(0, 1.53, 0); head.castShadow = true; g.add(head);
  const hh = new THREE.Mesh(new THREE.SphereGeometry(0.14, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), M(hat)); hh.position.set(0, 1.58, 0); g.add(hh);
  g.userData = { armL, armR };
  return g;
}
const workers = [[X(462), Z(781)], [X(462), Z(915)], [X(795), Z(781)], [X(795), Z(915)]].map(([x, z]) => {
  const p = makePerson(); p.position.set(x, 0.12, z); p.rotation.y = z < CZ ? -Math.PI / 2 : Math.PI / 2; return p; });
const stWorker = makePerson(); stWorker.position.set(X(650), 0.15, Z(1068)); stWorker.rotation.y = Math.PI / 2;
const operator = makePerson(0x2f6db3, 0xffffff); operator.position.set(CR.x + 0.55, 0, CR.z - 0.35); operator.rotation.y = Math.PI / 2;
// nút bấm cạnh công nhân
const btnL = cylAt(0.07, 0.06, M(0x3aa050, { emissive: 0x000000 }), X(484), 1.05, Z(781), 'x');
box(0.08, 1.0, 0.08, dark, X(484), 0.5, Z(781));
const btnR = cylAt(0.07, 0.06, M(0x3aa050, { emissive: 0x000000 }), X(773), 1.05, Z(781), 'x');
box(0.08, 1.0, 0.08, dark, X(773), 0.5, Z(781));

// ---------- xe nâng ----------
function makeForklift() {
  const g = new THREE.Group(); scene.add(g);
  const yel = M(0xdeaa2c, { roughness: 0.5 });
  box(1.5, 0.75, 1.0, yel, -0.35, 0.65, 0, g);
  box(0.35, 0.8, 1.0, M(0x4a4030), -1.2, 0.7, 0, g);                       // đối trọng
  box(0.4, 0.1, 0.5, M(0x333333), -0.5, 1.12, 0, g);                       // ghế
  box(0.08, 0.5, 0.4, M(0x333333), -0.7, 1.35, 0, g);
  for (const dx of [-1.0, 0.25]) for (const dz of [-0.45, 0.45]) box(0.06, 1.15, 0.06, dark, dx, 1.6, dz, g);   // khung bảo vệ
  box(1.35, 0.05, 1.0, dark, -0.38, 2.18, 0, g);
  for (const dx of [-0.9, 0.3]) for (const dz of [-0.52, 0.52]) cylAt(0.27, 0.2, M(0x1b1b1b), dx, 0.27, dz, 'z', g);
  for (const dz of [-0.35, 0.35]) box(0.1, 2.3, 0.1, M(0x555555, { metalness: 0.5 }), 0.5, 1.15, dz, g);   // khung nâng
  const forks = new THREE.Group(); g.add(forks);
  for (const dz of [-0.3, 0.3]) box(1.2, 0.05, 0.14, M(0x444444, { metalness: 0.5 }), 1.15, 0, dz, forks);
  box(0.06, 0.6, 0.8, M(0x444444), 0.55, 0.3, 0, forks);
  g.userData.forks = forks; return g;
}
const forklift = makeForklift();
const FL_OFF = 1.2;

// ---------- bao 50 kg (instanced) ----------
const bagTex = canvasTex(256, 170, (g) => {
  g.fillStyle = '#f4f1e8'; g.fillRect(0, 0, 256, 170);
  g.strokeStyle = 'rgba(0,0,0,0.05)'; for (let i = 0; i < 256; i += 4) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 170); g.stroke(); }
  g.fillStyle = '#2f6db3'; g.fillRect(0, 22, 256, 10); g.fillRect(0, 138, 256, 10);
  g.font = 'bold 44px DejaVu Sans'; g.textAlign = 'center'; g.fillText('KCP', 128, 100);
  g.font = 'bold 20px DejaVu Sans'; g.fillStyle = '#c0392b'; g.fillText('ĐƯỜNG · 50 KG', 128, 126);
});
const bagGeo = new RoundedBoxGeometry(BAG_L, BH, BAG_W, 3, 0.045);
const MAXB = 1500;
const bags = new THREE.InstancedMesh(bagGeo, new THREE.MeshStandardMaterial({ map: bagTex, roughness: 0.95 }), MAXB);
bags.castShadow = bags.receiveShadow = true; bags.frustumCulled = false; scene.add(bags);
let nb = 0; const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler();
function addBag(p, yaw = Math.PI / 2, sz = 1, roll = 0) {
  if (nb >= MAXB) return;
  _e.set(roll, yaw, 0); _q.setFromEuler(_e); _m.compose(p, _q, V(1, 1, sz)); bags.setMatrixAt(nb++, _m);
}
const badBag = new THREE.Mesh(bagGeo, new THREE.MeshStandardMaterial({ map: bagTex, color: 0xff9a8a, roughness: 0.9 }));
badBag.castShadow = true; scene.add(badBag); badBag.visible = false;

// ---------- sling (bao jumbo chứa 45 bao) ----------
function makeSling() {
  const g = new THREE.Group(); scene.add(g);
  const cloth = M(0xf2f2ee, { roughness: 1 });
  box(1.5, 0.03, 2.25, cloth, 0, 0.015, 0, g);
  const wallM = new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, opacity: 0.3, roughness: 1, side: THREE.DoubleSide, depthWrite: false });
  for (const dx of [-0.76, 0.76]) box(0.01, 0.7, 2.25, wallM, dx, 0.35, 0, g, false);
  for (const dz of [-1.13, 1.13]) box(1.5, 0.7, 0.01, wallM, 0, 0.35, dz, g, false);
  const strap = M(0xe9e4d4, { roughness: 0.9 });
  for (const dx of [-0.74, 0.74]) for (const dz of [-1.11, 1.11]) {
    box(0.09, 0.85, 0.09, strap, dx, 0.42, dz, g);
    const loop = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.025, 6, 16), strap); loop.position.set(dx, 0.95, dz); g.add(loop);
  }
  g.traverse(o => { if (o.material && !o.material.transparent) { o.material = o.material.clone(); o.material.transparent = true; } });
  return g;
}
function slingFade(g, k) { g.traverse(o => { if (o.material) o.material.opacity = (o.material.depthWrite === false ? 0.3 : 1) * k; }); g.visible = k > 0.01; }
const slingPool = Array.from({ length: 6 }, makeSling);
const stSling = makeSling(); stSling.rotation.y = Math.PI / 2; stSling.position.set(ST_C.x, 0.15, ST_C.z);
// thứ tự còn lại: lớp dưới trước, trong lớp hàng xa robot trước -> hút lớp trên, hàng gần (z nhỏ) trước
const ROWS = []; for (let L = 0; L < 5; L++) for (const r of [2, 1, 0]) ROWS.push([L, r]);
function slingBags(cx, baseY, cz, n, rot = false) {
  const R = Math.ceil(n / 3), rem = n % 3;
  for (let i = 0; i < R; i++) {
    const [L, r] = ROWS[i];
    for (let c = 0; c < ((i === R - 1 && rem) ? rem : 3); c++) {
      const y = baseY + 0.03 + BH / 2 + L * BH;
      if (!rot) addBag(V(cx + (c - 1) * 0.5, y, cz + (r - 1) * 0.75), Math.PI / 2);
      else addBag(V(cx + (r - 1) * 0.75, y, cz + (c - 1) * 0.5), 0);
    }
  }
}
function placeSlings(list) {   // [[x, n, k]]
  slingPool.forEach((g, i) => {
    const s = list[i];
    if (!s) { g.visible = false; return; }
    g.position.set(s[0], s[3] !== undefined ? s[3] : RH, CZ); slingFade(g, s[2] ?? 1);
    if ((s[2] ?? 1) > 0.5) slingBags(s[0], g.position.y, CZ, s[1]);
  });
}

// ---------- robot + đầu hút chân không 3 bao ----------
const robMat = M(0xd2541e, { roughness: 0.45, metalness: 0.25 }), robGray = M(0x9a9a9a, { roughness: 0.6 });
const rbase = cylAt(0.42, 0.7, robMat, ROBOT_B.x, 0.35, ROBOT_B.z);
const rturret = cylAt(0.32, 0.35, robMat, ROBOT_B.x, 0.85, ROBOT_B.z);
const rUpper = rod(0.13, robMat), rFore = rod(0.1, robMat), rLink = rod(0.06, robMat);
const rElbow = new THREE.Mesh(new THREE.SphereGeometry(0.16, 16, 12), robMat); scene.add(rElbow);
const headR = new THREE.Group(); scene.add(headR);
box(1.55, 0.1, 0.62, M(0x6a6f74, { metalness: 0.5 }), 0, 0.06, 0, headR);
const cups = [];
for (const dx of [-0.5, 0, 0.5]) for (const dz of [-0.16, 0.16]) cups.push(cylAt(0.07, 0.06, M(0x3aa050, { emissive: 0x000000 }), dx, -0.01, dz, 'y', headR));
const SH = V(ROBOT_B.x, 1.0, ROBOT_B.z), RL1 = 1.75, RL2 = 1.65;
function setRobot(hc, suction, carry, gray = false) {
  // hc: tâm đầu hút; carry: các bao đang hút [0,1,2]
  const mat = gray ? robGray : robMat;
  for (const m of [rbase, rturret, rUpper, rFore, rLink, rElbow]) m.material = mat;
  headR.position.copy(hc);
  const Wp = hc.clone().add(V(0, 0.55, 0));
  const dh = V(Wp.x - SH.x, 0, Wp.z - SH.z), h = dh.length(); dh.normalize();
  const v = Wp.y - SH.y, d = Math.min(Math.hypot(h, v), RL1 + RL2 - 0.01);
  const a1 = Math.atan2(v, h) + Math.acos(clamp((RL1 * RL1 + d * d - RL2 * RL2) / (2 * RL1 * d), -1, 1));
  const E = SH.clone().add(dh.clone().multiplyScalar(RL1 * Math.cos(a1))).add(V(0, RL1 * Math.sin(a1), 0));
  setRod(rUpper, SH, E); setRod(rFore, E, Wp); setRod(rLink, Wp, hc.clone().add(V(0, 0.1, 0))); rElbow.position.copy(E);
  cups.forEach(c => c.material.emissive.setHex(suction > 0.5 ? 0x1a6a20 : 0x000000));
  for (const j of carry) addBag(V(hc.x + (j - 1) * 0.5, hc.y - 0.02 - BH / 2, hc.z), Math.PI / 2);
}
const HC_REST = V(BX, BY + 0.6, DROP_Z);

// ---------- đường đi của bao (3D) ----------
const BAGY = BY + BH / 2;
const OUT = [V(BX, BAGY, DROP_Z), V(BX, BAGY, Z(660)), V(BX, BAGY, Z(597)), V(BX, TOP + BH / 2 + 0.01, Z(400))];
for (let i = 1; i <= 12; i++) { const a = Math.PI * (1 + 0.5 * i / 12); OUT.push(V(CURVE_C.x + CURVE_R * Math.cos(a), TOP + BH / 2 + 0.01, CURVE_C.z + CURVE_R * Math.sin(a))); }
OUT.push(V(TELE_X1, TOP + BH / 2 + 0.01, TELE_Z));
function pathLen(P) { let s = 0; for (let i = 0; i < P.length - 1; i++) s += P[i].distanceTo(P[i + 1]); return s; }
function pathAt(P, s) {
  for (let i = 0; i < P.length - 1; i++) {
    const L = P[i].distanceTo(P[i + 1]);
    if (s <= L || i === P.length - 2) {
      const k = clamp(s / L), d = P[i + 1].clone().sub(P[i]);
      return [P[i].clone().lerp(P[i + 1], k), Math.atan2(-d.z, d.x)];
    }
    s -= L;
  }
}
const OUT_L = pathLen(OUT);
const SEGS = { V: [pathLen(OUT.slice(0, 2)), pathLen(OUT.slice(0, 3))], S: [pathLen(OUT.slice(0, 3)), pathLen(OUT.slice(0, 4))] };

// ---------- vùng diện tích + cột cao 1,5 m ----------
const AREA_W = 13.258, AREA_D = (1158 - 323) * MMPX / 1000, STRIP_L = (1132 - 910) * MMPX / 1000, STRIP_W = (370 - 323) * MMPX / 1000;
const areaMat = new THREE.MeshBasicMaterial({ color: 0xd9774b, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide });
const areaMain = new THREE.Mesh(new THREE.PlaneGeometry(AREA_W, AREA_D), areaMat); areaMain.rotation.x = -Math.PI / 2;
areaMain.position.set(AREA_W / 2, 0.02, AREA_D / 2); scene.add(areaMain);
const areaStrip = new THREE.Mesh(new THREE.PlaneGeometry(STRIP_L, STRIP_W), areaMat); areaStrip.rotation.x = -Math.PI / 2;
areaStrip.position.set(AREA_W + STRIP_L / 2, 0.02, STRIP_W / 2); scene.add(areaStrip);
const edgeMat = new THREE.LineDashedMaterial({ color: 0xb2342c, dashSize: 0.4, gapSize: 0.25, transparent: true, opacity: 0 });
const edgePts = [V(0, 0.04, 0), V(AREA_W + STRIP_L, 0.04, 0), V(AREA_W + STRIP_L, 0.04, STRIP_W), V(AREA_W, 0.04, STRIP_W), V(AREA_W, 0.04, AREA_D), V(0, 0.04, AREA_D), V(0, 0.04, 0)];
const edge = new THREE.Line(new THREE.BufferGeometry().setFromPoints(edgePts), edgeMat); edge.computeLineDistances(); scene.add(edge);
const pole = cylAt(0.04, TOP, new THREE.MeshBasicMaterial({ color: 0xb2342c, transparent: true, opacity: 0 }), 5.9, TOP / 2, 0.6);

// ---------- tia cảm biến ----------
const beamMat = new THREE.LineDashedMaterial({ color: 0x107c80, dashSize: 0.12, gapSize: 0.08, transparent: true, opacity: 0 });
const beamRodMat = new THREE.MeshBasicMaterial({ color: 0x18c8c8, transparent: true, opacity: 0, depthWrite: false });
const beams = [0, 1, 2].map(() => rod(0.025, beamRodMat));
const hits = [0, 1, 2].map(() => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 8), beamRodMat); scene.add(m); return m; });
const coneMat = new THREE.MeshBasicMaterial({ color: 0x3ab050, transparent: true, opacity: 0, depthWrite: false });
const cone = new THREE.Mesh(new THREE.ConeGeometry(0.35, 1, 24, 1, true), coneMat); scene.add(cone);
function setBeam(i, a, b) { setRod(beams[i], a, b); hits[i].position.copy(b); }

// ---------- nhãn gắn vào vật thể ----------
const labs = {};
function lab(id, text, color, flat = false) {
  const d = document.createElement('div'); d.className = 'lab' + (flat ? ' flat' : ''); d.innerHTML = text;
  d.style.color = color; d.style.borderColor = color; document.getElementById('labs').appendChild(d); labs[id] = d;
}
const _v = new THREE.Vector3();
function showLab(id, p, k, dx = 0) {
  const d = labs[id]; _v.copy(p).project(camera);
  if (k <= 0 || _v.z > 1) { d.style.opacity = 0; return; }
  d.style.left = ((_v.x + 1) / 2 * W + dx) + 'px'; d.style.top = ((1 - _v.y) / 2 * H - 16) + 'px'; d.style.opacity = k;
}
const EL = { L: '(1) Băng con lăn sling – trái', R: '(2) Băng con lăn sling – phải', C: '(3) Cell robot – hút chân không',
  V: '(4) Băng tải vệ sinh bao', S: '(5) Băng tải ra', K: '(6) Băng cong 90°', T: '(7) Băng tải ống lồng', X: '(8) Thùng xe 34T', M: '(9) Trạm xả tay dự phòng' };
for (const k in EL) lab(k, EL[k], CSS(k));
lab('fork', 'XE NÂNG', '#1d2b3a'); lab('btn', 'BẤM NÚT', '#b2342c'); lab('chk', 'kiểm tra bao: ngay ngắn, không rách', '#b2342c');
lab('out', 'công nhân lấy sling rỗng ra', '#b2342c'); lab('wait', 'rỗng – chờ', CSS('R')); lab('wait2', 'chờ hút', CSS('L'));
lab('dw', '13,26 m (bản vẽ 13.258 mm)', '#b2342c', true); lab('dd', `≈ ${AREA_D.toFixed(2).replace('.', ',')} m`, '#b2342c', true);
lab('ds', `≈ ${STRIP_L.toFixed(1).replace('.', ',')} m`, '#b2342c', true); lab('h15', 'cao nhất 1,5 m', '#b2342c');
lab('lr', 'rải trái → phải', '#b2342c'); lab('l9', '9 lớp = 117 cm', '#b2342c'); lab('back', '← thụt lại 75 cm', CSS('T'));
lab('lim', 'giới hạn: cách trần 30 cm', '#b2342c'); lab('sa', '(A) định vị thùng xe', CSS('T')); lab('sb', '(B) vị trí bao', CSS('T'));
lab('bad', 'bao đặt lệch', '#b2342c'); lab('cr', 'phòng điều khiển (vị trí minh họa)', '#1d2b3a');
lab('n1', '1', '#b04030', true); lab('n2', '2', '#b04030', true); lab('n3', '3', '#b04030', true);
lab('via', 'đi thẳng qua cell – cùng trục băng tải ra', '#b2342c'); lab('robx', 'ROBOT KHÔNG HOẠT ĐỘNG', '#b2342c');
lab('reach', 'vươn tối đa 18 m', CSS('T')); lab('stop', 'NÚT DỪNG', '#b2342c');

// ---------- chữ phủ ----------
const ui = {}; for (const id of ['chap', 'sub', 'card', 'steps', 'counter', 'stamp', 'panel', 'note']) ui[id] = document.getElementById(id);
const last = {};
function setUI(id, html, k) {
  if (last[id] !== html) { ui[id].innerHTML = html; last[id] = html; }
  ui[id].style.opacity = clamp(k);
}
function subs(t, items) { for (const [a, b, s] of items) if (t >= a && t < b) { setUI('sub', s, seg(t, a, a + 0.35)); return; } setUI('sub', '', 0); }
function card(code, title, lines, k) {
  ui.card.style.setProperty('--c', CSS(code));
  setUI('card', `<span class="n">${EL[code].match(/\((\d)\)/)[1]}</span><h3>${title}</h3>` + lines.map((l, i) => i === lines.length - 1 && l.startsWith('~') ? `<div class="m">${l.slice(1)}</div>` : `<div>${l}</div>`).join(''), k);
}
function camSet(p, l) { camera.position.copy(p); camera.lookAt(l); camera.updateMatrixWorld(true); }
function camKeys(t, keys) {   // [[t, pos[], look[]]]
  let i = 0; while (i < keys.length - 1 && t >= keys[i + 1][0]) i++;
  const a = keys[i], b = keys[Math.min(i + 1, keys.length - 1)];
  const k = b[0] > a[0] ? seg(t, a[0], b[0]) : 1;
  camSet(V(...a[1]).lerp(V(...b[1]), k), V(...a[2]).lerp(V(...b[2]), k));
}

// ---------- bao trên băng ----------
function beltBag(s) { if (s < 0 || s > OUT_L) return; const [p, yaw] = pathAt(OUT, s); addBag(p, yaw); }

// ---------- kế hoạch chất xe (giống video 2D) ----------
const FULLR = 14, NROW = 16, rowLayers = r => r < FULLR ? 9 : 5;
const PLAN = []; (function () {
  let t = 2.5;
  for (let r = 0; r < NROW; r++) {
    const n = 5 * rowLayers(r); let times, dur;
    if (r === 0) { times = []; for (let i = 0; i < n; i++) times.push(i < 5 ? t + 0.7 * (i + 1) : t + 3.5 + 0.1 * (i - 4)); dur = 3.5 + 0.1 * (n - 5); }
    else { dur = r === 1 ? 2.2 : 0.32; times = []; for (let i = 0; i < n; i++) times.push(t + dur * (i + 1) / n); }
    PLAN.push([r, t, dur, times]);
    t += dur + (r === 0 ? 1.4 : r === 1 ? 0.3 : 0.08);
  }
})();
const T_DONE = PLAN[NROW - 1][1] + PLAN[NROW - 1][2];
const rowX = r => FW - 0.75 * r - 0.375, colZ = c => TELE_Z + (c - 2) * 0.47, layY = k => BED + BH / 2 + k * BH;
function truckState(t, freezeN = null) {
  let total = 0, cur = 0, head = null, inHand = false;
  for (const [r, t0, dur, times] of PLAN) {
    let n = times.filter(x => x <= t).length;
    if (freezeN !== null && r === 0) n = Math.min(n, freezeN);
    if (freezeN !== null && r > 0) n = 0;
    total += n; if (n) cur = r;
    for (let i = 0; i < n; i++) addBag(V(rowX(r), layY(Math.floor(i / 5)), colZ(i % 5)), 0, 0.94);
    if ((t >= t0 && t < t0 + dur) || (freezeN !== null && r === 0)) {
      const j = Math.min(n, times.length - 1);
      head = V(rowX(r) - 0.7, layY(Math.floor(j / 5)) + 0.32, colZ(j % 5)); inHand = dur > 2;
    }
  }
  if (!head) {   // đang thụt lại hoặc chưa bắt đầu / đã xong
    let face;
    if (t < PLAN[0][1]) face = lerp(TELE_X1 + 1.0, rowX(0) - 0.7, seg(t, 0.2, 2.4));
    else if (t >= T_DONE) face = lerp(rowX(NROW - 1) - 0.7, TELE_X1 + 1.0, seg(t, T_DONE + 0.4, T_DONE + 2.4));
    else { for (let i = 0; i < PLAN.length - 1; i++) { const e = PLAN[i][1] + PLAN[i][2]; if (t >= e && t < PLAN[i + 1][1]) face = lerp(rowX(i) - 0.7, rowX(i + 1) - 0.7, seg(t, e, PLAN[i + 1][1])); } }
    head = V(face, TOP + 0.1, TELE_Z);
  }
  return { total, cur, head, inHand };
}

// ---------- chu kỳ hút 3 bao, thả từng bao ----------
const PH = [['a', 2.9], ['b', 0.9], ['c', 1.7], ['d', 0.6], ['e', 1.6], ['f', 0.6], ['g', 1.6], ['h', 0.6]];
const PH_SUM = PH.reduce((s, p) => s + p[1], 0);
const STEP_OF = { a: 0, b: 0, c: 1, d: 2, e: 3, f: 3, g: 4, h: 4 };
const rowZ = r => CZ + (r - 1) * 0.75;
function topY(n) { const R = Math.round(n / 3); const L = R > 0 ? ROWS[R - 1][0] : 0; return RH + 0.03 + (L + 1) * BH; }
function pickCycle(t, t0, T, r, nBefore) {
  const sc = T / PH_SUM, mk = {}; let a = t0;
  for (const [n, v] of PH) { mk[n] = [a, a + v * sc]; a += v * sc; }
  const pickH = V(POS.C, topY(nBefore) + 0.06, rowZ(r));
  const over = [0, 1, 2].map(j => V(BX - (j - 1) * 0.5, BY + BH + 0.06, DROP_Z));
  const drops = [mk.d[0], mk.f[0], mk.h[0]];
  const start = over[2];
  if (t < t0) return { hc: start, carry: [], suc: 0, drops, ph: null, lifted: false };
  for (const [n] of PH) {
    const [s, e] = mk[n];
    if (t < e) {
      const u = seg(t, s, e);
      if (n === 'a') { const p = start.clone().lerp(pickH, u); p.y += 0.6 * Math.sin(Math.PI * u); return { hc: p, carry: [], suc: 0, drops, ph: n, lifted: false }; }
      if (n === 'b') return { hc: pickH, carry: [], suc: 1, drops, ph: n, lifted: u > 0.6 };
      if (n === 'c') { const p = pickH.clone().lerp(over[0], u); p.y += 0.5 * Math.sin(Math.PI * u); return { hc: p, carry: [0, 1, 2], suc: 1, drops, ph: n, lifted: true }; }
      if (n === 'd') return { hc: over[0], carry: [1, 2], suc: 1, drops, ph: n, lifted: true };
      if (n === 'e') return { hc: over[0].clone().lerp(over[1], seg(t, s + (e - s) * 0.45, e)), carry: [1, 2], suc: 1, drops, ph: n, lifted: true };
      if (n === 'f') return { hc: over[1], carry: [2], suc: 1, drops, ph: n, lifted: true };
      if (n === 'g') return { hc: over[1].clone().lerp(over[2], seg(t, s + (e - s) * 0.45, e)), carry: [2], suc: 1, drops, ph: n, lifted: true };
      return { hc: over[2], carry: [], suc: 0, drops, ph: n, lifted: true };
    }
  }
  return { hc: over[2], carry: [], suc: 0, drops, ph: null, lifted: true };
}

// ================= các cảnh =================
function resetFrame() {
  nb = 0; for (const k in labs) labs[k].style.opacity = 0;
  for (const id in ui) ui[id].style.opacity = 0;
  forklift.visible = false; badBag.visible = false;
  areaMat.opacity = 0; edgeMat.opacity = 0; pole.material.opacity = 0; fenceMat.opacity = 0.16;
  beamMat.opacity = 0; beamRodMat.opacity = 0; coneMat.opacity = 0; limitPlane.material.opacity = 0;
  btnL.material.emissive.setHex(0); btnR.material.emissive.setHex(0); stopBtn.material.emissive.setHex(0);
  stSling.visible = true; slingFade(stSling, 1); ui.stamp.style.top = '42%'; ui.stamp.style.left = '50%';
  workers.forEach(w => { w.userData.armL.rotation.z = 0; w.userData.armL.position.y = 1.1; });
}
function chap(t, s) { setUI('chap', s, seg(t, 0, 0.4)); }
function defaultScene(t) {
  placeSlings([[POS.C, 45], [POS.R1, 45], [POS.R0, 45]]);
  slingBags(ST_C.x, 0.15, ST_C.z, 45, true);
  setRobot(HC_REST, 0, []); setTele(TELE_X1 + 1.0, null);
}
function brushSpin(t) { brushes.forEach(b => b.rotation.x = t * 9); }

function sOverview(t, D) {
  camKeys(t, [[0, [-6, 17, 29], [11, 0, 8]], [14, [6, 14, 30], [13, 0, 7]]]);
  defaultScene(t); brushSpin(t);
  const anchors = { L: V(2.7, 1.3, CZ), R: V(10.6, 1.3, CZ), C: V(POS.C, 2.9, cz0), V: V(BX, 1.6, Z(628)), S: V(BX, 1.7, Z(470)),
    K: V(CURVE_C.x - 0.6, 1.9, CURVE_C.z - 0.9), T: V(13.5, 2.0, TELE_Z), X: V(24.5, 3.8, TELE_Z), M: V(ST_C.x, 3.2, ST_C.z - 1.0) };
  const DX = { C: -150, V: 150, S: -40, K: -60 };
  Object.keys(anchors).forEach((k, i) => showLab(k, anchors[k], seg(t, 1.5 + i * 1.1, 1.9 + i * 1.1), DX[k] || 0));
  chap(t, 'TỔNG QUAN – MINH HỌA 3D');
  subs(t, [[0, 1.5, 'Máy depal bao tự động – dựng 3D theo bản vẽ 20/10/2026'], [1.5, 11.5, 'Chín cụm chính, đánh số theo hành trình của bao đường 50 kg'],
           [11.5, D + 1, 'Cao độ từng băng tải, sàn xe: minh họa – chỉ biết điểm cao nhất 1,5 m']]);
}
function sArea(t, D) {
  camKeys(t, [[0, [5, 17, 34], [12, 0, 8]], [2.5, [9, 34, 22], [10, 0, 9]], [D, [9, 34, 21], [10, 0, 9]]]);
  defaultScene(t);
  const k = seg(t, 1.5, 3); areaMat.opacity = 0.32 * k; edgeMat.opacity = k;
  showLab('dw', V(AREA_W / 2, 0.1, -0.9), seg(t, 3, 3.5)); showLab('dd', V(-1.6, 0.1, AREA_D / 2), seg(t, 3.5, 4));
  showLab('ds', V(AREA_W + STRIP_L / 2, 0.1, -0.9), seg(t, 4.5, 5));
  pole.material.opacity = seg(t, 7, 7.5); showLab('h15', V(5.9, TOP + 0.1, 0.6), seg(t, 7, 7.5));
  setUI('card', '', 0);
  ui.card.style.setProperty('--c', '#b04030');
  setUI('card', `<h3>Diện tích chiếm trong kho</h3><div>Khung chính ≈ 13,26 × ${AREA_D.toFixed(2).replace('.', ',')} m ≈ ${(AREA_W * AREA_D).toFixed(0)} m²</div>` +
    `<div>Dải băng ra xe ≈ ${STRIP_L.toFixed(1).replace('.', ',')} × ${STRIP_W.toFixed(1).replace('.', ',')} m ≈ ${(STRIP_L * STRIP_W).toFixed(0)} m²</div>` +
    `<div><b style="font-size:22px;color:#b04030">Tổng ≈ ${(AREA_W * AREA_D + STRIP_L * STRIP_W).toFixed(0)} m²</b></div>` +
    `<div class="m">không tính lối đi xe nâng, chỗ đậu xe · đo trên bản vẽ (ước tính)</div><div><b style="color:#107c80">Điểm cao nhất băng tải: 1,5 m</b></div>`, seg(t, 5, 5.5));
  chap(t, 'DIỆN TÍCH TRONG KHO');
  subs(t, [[0, 5, 'Phần hệ thống chiếm chỗ trong kho (vùng cam)'], [5, 7, 'Tổng khoảng 262 m², chưa tính lối đi xe nâng và chỗ đậu xe'],
           [7, D + 1, 'Điểm cao nhất của hệ thống băng tải: 1,5 m (Phon-Tech)']]);
}

const FLOW = {
  A: { keys: [[0.3, -3.5], [2.6, POS.L0], [3.2, POS.L0], [4.6, POS.L2], [9.2, POS.L2], [10.8, POS.C], [14.0, POS.C], [15.6, POS.R2], [20.0, POS.R2], [22.0, POS.L2]], dep: [11.0, 13.8], out: [22.2, 23.6], show: 0.3 },
  B: { keys: [[4.4, -3.5], [6.7, POS.L0], [7.3, POS.L0], [8.3, POS.L1], [9.4, POS.L1], [10.8, POS.L2], [16.0, POS.L2], [17.4, POS.C], [20.0, POS.C], [22.0, POS.L1]], dep: [17.6, 19.8], out: [22.2, 23.6], show: 4.4 },
  R1: { keys: [[0, POS.R1], [23.8, POS.R1], [25.6, POS.C]], dep: null, out: null, show: 0 },
  R0: { keys: [[0, POS.R0], [23.9, POS.R0], [25.6, POS.R2]], dep: null, out: null, show: 0 },
};
const nbag = (t, a, b) => Math.round(lerp(45, 0, lin(t, a, b)) / 3) * 3;
function sFlow(t, D) {
  camKeys(t, [[0, [9, 34, 21], [10, 0, 9]], [1.5, [2.5, 8.5, 22.5], [5.6, 0.5, 11.6]], [D, [3.5, 8.5, 22.5], [6.0, 0.5, 11.6]]]);
  brushSpin(t);
  const list = [];
  for (const k of ['A', 'B', 'R1', 'R0']) {
    const f = FLOW[k]; if (t < f.show) continue;
    const x = kx(t, f.keys), n = f.dep ? nbag(t, f.dep[0], f.dep[1]) : 45;
    let kk = 1, y = RH;
    if (f.out) { kk = 1 - seg(t, f.out[0] + 0.6, f.out[1]); y = RH + 0.8 * seg(t, f.out[0], f.out[1]); }
    // đang trên càng xe nâng
    if (k === 'A' && t < 3.2) y = RH + 0.15 * (1 - seg(t, 2.6, 3.2));
    if (k === 'B' && t >= 4.4 && t < 7.3) y = RH + 0.15 * (1 - seg(t, 6.7, 7.3));
    list.push([x, n, kk, y]);
  }
  placeSlings(list);
  slingBags(ST_C.x, 0.15, ST_C.z, 45, true);
  // xe nâng
  let fx = null, fy = 0.15;
  if (t >= 0.3 && t < 3.2) { fx = kx(t, FLOW.A.keys) - FL_OFF; fy = RH + 0.15 * (1 - seg(t, 2.6, 3.2)) - 0.03; }
  else if (t >= 3.2 && t < 4.3) { fx = lerp(POS.L0 - FL_OFF, -7, seg(t, 3.2, 4.3)); fy = RH - 0.1; }
  else if (t >= 4.4 && t < 7.3) { fx = kx(t, FLOW.B.keys) - FL_OFF; fy = RH + 0.15 * (1 - seg(t, 6.7, 7.3)) - 0.03; }
  else if (t >= 7.3 && t < 8.4) { fx = lerp(POS.L0 - FL_OFF, -7, seg(t, 7.3, 8.4)); fy = RH - 0.1; }
  if (fx !== null) { forklift.visible = true; forklift.position.set(fx, 0, CZ); forklift.userData.forks.position.y = fy; showLab('fork', V(fx - 0.3, 2.6, CZ), 1); }
  // robot: hút nhanh trong lúc tua
  let hc = HC_REST.clone(), carry = [];
  for (const k of ['A', 'B']) { const [a, b] = FLOW[k].dep; if (t >= a && t < b) {
    const u = 0.5 - 0.5 * Math.cos(2 * Math.PI * 1.6 * (t - a)); hc = HC_REST.clone().lerp(V(POS.C, 1.3, CZ - 0.5), u); carry = u < 0.5 ? [0, 1, 2] : [];
    for (let i = 0; i * 0.17 < t - a; i++) beltBag((t - a - i * 0.17) * 3.2);
  } }
  setRobot(hc, carry.length ? 1 : 0, carry); setTele(TELE_X1 + 1.0, null);
  // nút bấm
  for (const [tp, btn] of [[8.8, btnL], [15.8, btnL]]) if (t >= tp - 0.2 && t < tp + 1.2) {
    btn.material.emissive.setHex(0x3aff60); showLab('btn', V(X(484), 1.4, Z(781)), 1);
    workers[0].userData.armL.rotation.z = -0.9;
  }
  showLab('chk', V(X(462), 2.1, Z(781)), seg(t, 7.6, 8.0) * (1 - seg(t, 8.6, 8.9)));
  showLab('wait2', V(POS.L2, 1.6, CZ), seg(t, 10.8, 11.2) * (1 - seg(t, 15.6, 16.0)));
  showLab('wait', V(POS.R2, 1.6, CZ), seg(t, 15.6, 16.0) * (1 - seg(t, 19.6, 20.0)));
  showLab('out', V(3.6, 2.1, CZ), seg(t, 22.2, 22.5) * (1 - seg(t, 23.6, 23.9)));
  if ((t >= 11 && t < 13.8) || (t >= 17.6 && t < 19.8)) setUI('counter', 'HÚT 45 BAO · TUA NHANH >>', 1);
  card('L', 'Băng con lăn sling', ['mỗi bên 3 vị trí, 2 sling đầy', 'sling chỉ vào khi công nhân bấm nút', '~Phon-Tech xác nhận 04/11/2026'], seg(t, 1.0, 1.5) * (1 - seg(t, 9.6, 10.0)));
  chap(t, '(1)(2) SLING VÀO – SLING RỖNG RA');
  subs(t, [[0, 4.4, 'Xe nâng đưa sling đầy vào băng con lăn bên trái'], [4.4, 7.6, 'Xe nâng đặt sling thứ hai – mỗi bên 2 sling'],
           [7.6, 10.8, 'Công nhân kiểm tra bao ngay ngắn, không rách, rồi bấm nút'], [10.8, 14.0, 'Sling vào cell, máy hút hết 45 bao (tua nhanh)'],
           [14.0, 16.0, 'Sling rỗng sang vị trí chờ bên phải'], [16.0, 20.0, 'Bấm nút: sling thứ hai vào hút'],
           [20.0, 22.2, 'Hút xong, cả 2 sling rỗng trả về bên trái'], [22.2, 23.8, 'Công nhân lấy 2 sling rỗng ra'],
           [23.8, D + 1, 'Bên phải làm giống hệt – lúc đó xe nâng nạp 2 sling mới bên trái']]);
}

const CYC = [[1.0, 12.0, 0, 45], [13.4, 5.0, 1, 42]];
const STEPS = ['Hút 3 bao – 1 hàng ngang dài 1,5 m', 'Đưa 3 bao tới đầu băng tải', 'Thả bao thứ 1', 'Dịch sang, thả bao thứ 2', 'Dịch sang, thả bao thứ 3'];
function sPick(t, D) {
  fenceMat.opacity = 0.05;
  camKeys(t, [[0, [3.5, 8.5, 22.5], [6.0, 0.5, 11.6]], [1.2, [11.2, 5.4, 12.6], [6.5, 0.9, 10.2]], [D, [11.0, 5.5, 12.4], [6.5, 0.9, 10.2]]]);
  brushSpin(t);
  let picked = 0, st = { hc: HC_REST, carry: [], suc: 0, ph: null }, drops = [];
  for (const [t0, T, r, nBefore] of CYC) {
    const c = pickCycle(t, t0, T, r, nBefore);
    const v = 0.55 * 12 / T;
    c.drops.forEach(td => drops.push([td, v]));
    if (t >= t0 && t < t0 + T + 0.4) st = c;
    if (t >= t0 && c.lifted) picked += 3;
  }
  if (t >= 18.6) { const u = 0.5 - 0.5 * Math.cos(2 * Math.PI * 1.8 * (t - 18.6)); st = { hc: HC_REST.clone().lerp(V(POS.C, 1.3, CZ - 0.4), u), carry: u < 0.5 ? [0, 1, 2] : [], suc: 1, ph: null };
    picked = 6 + Math.floor(lin(t, 18.6, D) * 4) * 3; for (let i = 0; i * 0.25 < t - 18.6; i++) drops.push([18.6 + i * 0.25, 2.5]); }
  const n = 45 - picked;
  placeSlings([[POS.C, n], [POS.R1, 45], [POS.R0, 45]]);
  slingBags(ST_C.x, 0.15, ST_C.z, 45, true);
  setRobot(st.hc, st.suc, st.carry); setTele(TELE_X1 + 1.0, null);
  if (t < 13.4) st.carry.forEach(j => showLab('n' + (j + 1), V(st.hc.x + (j - 1) * 0.5, st.hc.y + 0.12, st.hc.z), 1));
  for (const [td, v] of drops) if (t >= td) beltBag((t - td) * v);
  const cur = st.ph ? STEP_OF[st.ph] : null;
  const html = '<h4>MỘT LẦN HÚT = 3 BAO</h4>' + STEPS.map((s, i) => `<div class="${i === cur ? 'on' : (cur !== null && i < cur ? 'done' : '')}">(${i + 1}) ${s}</div>`).join('') +
    '<div class="f">thả lần lượt từng bao: chốt với Phon-Tech sáng 05/11/2026</div>';
  setUI('steps', html, seg(t, 0.8, 1.2) * (1 - seg(t, 18.4, 18.8)));
  setUI('counter', `CÒN ${n}/45 BAO TRÊN SLING`, 1);
  chap(t, '(3) HÚT 3 BAO – THẢ TỪNG BAO');
  const c0 = CYC[0][0], s0 = CYC[0][1] / PH_SUM, m = [c0]; for (const [, v] of PH) m.push(m[m.length - 1] + v * s0);
  subs(t, [[0, c0, 'Cell robot: đầu hút chân không (Phon-Tech xác nhận)'], [c0, m[2], 'Đầu hút chân không hút 1 hàng 3 bao nằm ngang, dài 1,5 m'],
           [m[2], m[3], 'Đưa cả 3 bao tới đầu băng tải'], [m[3], m[5], 'Thả bao thứ 1 xuống băng tải'], [m[5], m[7], 'Dịch sang, thả bao thứ 2'],
           [m[7], 13.4, 'Dịch sang, thả bao thứ 3 – băng tải đưa bao đi'], [13.4, 18.6, 'Lần hút thứ 2 – nhịp thực tế 12–13,5 giây cho 3 bao'],
           [18.6, D + 1, '15 lần hút cho 1 sling 45 bao (5 lớp × 3 hàng)']]);
}

const JT = [['V', 0, 3.5], ['S', 3.5, 7.0], ['K', 7.0, 9.0], ['T', 9.0, 14.0]];
const JCARD = { V: ['Băng tải vệ sinh bao', ['chổi quét sạch bụi trên bao', '~Phon-Tech xác nhận 04/11/2026']], S: ['Băng tải ra', ['đưa bao ra khỏi cell, lên cao 1,5 m', '~cao độ đoạn đầu: minh họa']],
  K: ['Băng cong 90°', ['đổi hướng bao về phía xe']], T: ['Băng tải ống lồng', ['vươn ra / thụt vào, tối đa 18 m', 'có cảm biến định vị', '~Phon-Tech xác nhận 04/11/2026']] };
function sJourney(t, D) {
  brushSpin(t * 1.5);
  const ends = { V: SEGS.V[1], S: SEGS.S[1], K: OUT_L - (TELE_X1 - CURVE_C.x), T: OUT_L };
  let s = 0, prev = 0;
  for (const [k, a, b] of JT) { if (t >= a) s = lerp(prev, ends[k], ss((t - a) / (b - a))); prev = ends[k]; }
  s = Math.max(s, 0.01);
  const [p] = pathAt(OUT, s);
  const kz = clamp((p.x - BX) / 1.3);
  const off = V(lerp(3.2, -1.5, kz), 2.2, lerp(1.6, 4.2, kz));
  camSet(p.clone().add(off), p.clone().add(V(lerp(0, 1.5, kz), 0, lerp(-1.2, 0, kz))));
  placeSlings([[POS.C, 36], [POS.R1, 45], [POS.R0, 45]]); slingBags(ST_C.x, 0.15, ST_C.z, 45, true);
  setRobot(HC_REST, 0, []); setTele(TELE_X1 + 1.0, null);
  for (const d of [-1.3, 0, 1.3, 2.6, 3.9]) beltBag(s + d);
  for (const [k, a, b] of JT) { const kk = seg(t, a, a + 0.4) * (k === 'T' ? 1 : 1 - seg(t, b - 0.2, b + 0.1)); if (kk > 0) card(k, JCARD[k][0], JCARD[k][1], kk); }
  chap(t, '(4)–(7) VỆ SINH BAO, RA XE');
  subs(t, [[0, 3.5, 'Băng tải vệ sinh: chổi quét sạch bụi trên bao'], [3.5, 7, 'Băng tải ra đưa bao khỏi cell, lên cao 1,5 m'],
           [7, 9, 'Băng cong 90° đổi hướng bao về phía xe'], [9, D + 1, 'Băng tải ống lồng đưa bao vào thùng xe']]);
}

function sTruck(t, D) {
  camKeys(t, [[0, [13, 7, 7.5], [21, 1.5, 0.5]], [3, [25.0, 6.8, 5.6], [29.4, 1.5, 0.5]], [10.2, [25.0, 6.8, 5.6], [29.4, 1.5, 0.5]],
              [11.6, [27.2, 3.0, 6.2], [29.4, 1.9, 0.5]], [14.2, [27.2, 3.0, 6.2], [29.4, 1.9, 0.5]], [16.5, [17.5, 9.5, 9.5], [25, 1.6, 0.5]], [D, [17.0, 9.8, 9.8], [25, 1.6, 0.5]]]);
  placeSlings([[POS.C, 45], [POS.R1, 45], [POS.R0, 45]]);
  setRobot(HC_REST, 0, []);
  const S = truckState(t);
  setTele(S.head.x - 0.6, S.head);
  if (S.inHand) addBag(S.head.clone().add(V(0.45, -0.22, 0)), 0, 0.94);
  for (let i = 0; i < 6; i++) { const x = lerp(TELE_X1, S.head.x - 0.6, ((t * 0.9 + i / 6) % 1)); addBag(V(x, TOP + BH / 2 + 0.01, TELE_Z), 0); }
  showLab('reach', V(TELE_X1 + 2, TOP + 0.9, TELE_Z), seg(t, 0.3, 0.7) * (1 - seg(t, 2.6, 3)));
  showLab('lr', V(rowX(0) - 0.3, BED + 2.0, TELE_Z), seg(t, 2.6, 3.0) * (1 - seg(t, 9.8, 10.1)));
  showLab('l9', V(rowX(0) - 0.4, BED + 0.9, TELE_Z + 1.3), seg(t, 10.0, 10.4) * (1 - seg(t, 13.6, 14.0)), -110);
  showLab('back', V(rowX(1), BED + 1.8, TELE_Z), seg(t, 10.0, 10.4) * (1 - seg(t, 11.4, 11.7)));
  limitPlane.material.opacity = 0.22 * seg(t, 11.6, 12.0) * (1 - seg(t, 15, 15.4));
  showLab('lim', V(rowX(2), BED + 1.95, TELE_Z + 1.2), seg(t, 11.6, 12.0) * (1 - seg(t, 15, 15.4)));
  setUI('counter', `ĐÃ CHẤT ${S.total}/680 BAO · HÀNG ${S.cur + 1}/16`, 1);
  if (t > T_DONE + 0.4) setUI('stamp', 'XONG 1 XE · 680 BAO · 34 TẤN', seg(t, T_DONE + 0.4, T_DONE + 0.7));
  setUI('note', 'đã bỏ bạt để nhìn vào trong thùng · sàn xe cao 1,3 m: minh họa', 1);
  chap(t, '(7)(8) BĂNG ỐNG LỒNG TỰ CHẤT LÊN XE');
  subs(t, [[0, 2.5, 'Băng tải ống lồng vươn vào sát đầu thùng xe (tối đa 18 m)'],
           [2.5, 10, 'Đầu băng tự rải bao từ trái sang phải, đủ 5 bao mới lên lớp trên'],
           [10, 11.6, 'Đủ 9 lớp = 45 bao, băng thụt lại 75 cm để chất hàng tiếp theo'],
           [11.6, 15.4, 'Chất cao tối đa: cách trần xe 30 cm'],
           [15.4, T_DONE + 0.4, 'Lặp lại tới hàng 16 – không cần người trong thùng xe'],
           [T_DONE + 0.4, D + 1, '14 hàng × 45 bao + 2 hàng × 25 bao = 680 bao = 34 tấn']]);
}

function sSensor(t, D) {
  const truckCam = [[26.4, 5.2, 2.9], [29.7, 1.5, 0.4]], crCam = [[CR.x - 1.0, 2.0, CR.z + 2.6], [CR.x - 0.2, 1.15, CR.z - 1.1]];
  const keys = [[0, [17.0, 9.8, 9.8], [25, 1.6, 0.5]], [1.5, ...truckCam], [10, ...truckCam], [10.01, ...crCam], [13, ...crCam], [13.01, ...truckCam], [15.5, ...truckCam], [15.51, ...crCam], [D, ...crCam]];
  camKeys(t, keys);
  placeSlings([[POS.C, 45], [POS.R1, 45], [POS.R0, 45]]);
  setRobot(HC_REST, 0, []);
  const bad = t >= 13;
  const S = truckState(PLAN[0][1] + 3.0 + Math.min(t, 6) * 0.22, 12);
  setTele(S.head.x - 0.6, S.head);
  const hp = S.head.clone().add(V(0.3, 0.12, 0));
  const kA = seg(t, 2, 2.6) * (t < 10 ? 1 : 0);
  if (kA > 0) { beamRodMat.opacity = 0.85 * kA;
    setBeam(0, hp, V(hp.x + 0.25, hp.y, TELE_Z - TW / 2 + 0.03)); setBeam(1, hp, V(hp.x + 0.25, hp.y, TELE_Z + TW / 2 - 0.03)); setBeam(2, hp, V(FW, hp.y + 0.3, hp.z));
    showLab('sa', V(hp.x, hp.y + 0.5, TELE_Z - 1.3), kA); }
  const slot = V(rowX(0), layY(2), colZ(2));
  const kB = seg(t, 6, 6.6) * ((t < 10 || (t >= 13 && t < 15.5)) ? 1 : 0);
  if (kB > 0) { coneMat.opacity = 0.35 * kB; coneMat.color.setHex(bad ? 0xd03a30 : 0x3ab050);
    const a = hp, b = slot.clone().add(V(0, 0.1, 0)), d = b.clone().sub(a);
    cone.position.copy(a).add(b).multiplyScalar(0.5); cone.quaternion.setFromUnitVectors(V(0, -1, 0), d.clone().normalize()); cone.scale.set(1, d.length(), 1);
    showLab('sb', V(hp.x - 0.4, hp.y + 0.45, TELE_Z + 1.1), kB); }
  else coneMat.opacity = 0;
  if (bad) { badBag.visible = true; badBag.position.set(slot.x - 0.08, slot.y, slot.z + 0.12); badBag.rotation.set(0, 0.35, 0.12); badBag.scale.set(1, 1, 0.94);
    if (t < 15.5) showLab('bad', V(slot.x, slot.y + 0.4, slot.z + 0.6), 1); }
  drawMonitor(bad && t >= 15.5 ? 'bad' : 'ok', bad && (Math.floor(t * 3) % 2 === 0));
  if (t >= 10) showLab('cr', V(CR.x, 2.9, CR.z), t < 13 || t >= 15.5 ? 1 : 0);
  const press = t >= 17.4 && t < 18.6;
  if (t >= 15.5) showLab('stop', V(CR.x + 0.25, 1.15, CR.z - 0.7), 1);
  stopBtn.material.emissive.setHex(press ? 0xff2010 : 0x000000);
  operator.userData.armR.rotation.x = press ? -0.9 : 0;
  if (t >= 18) { ui.stamp.style.top = '20%'; ui.stamp.style.left = '28%'; setUI('stamp', 'DỪNG MÁY', seg(t, 18, 18.3)); }
  setUI('counter', `ĐÃ CHẤT ${S.total}/680 BAO`, t < 10 || (t >= 13 && t < 15.5) ? 1 : 0);
  if (t >= 18) setUI('note', 'bấm dừng khi cảm biến sai: giả định KCP – cần Phon-Tech xác nhận', 1);
  else if (t >= 10 && (t < 13 || t >= 15.5)) setUI('note', 'vị trí phòng điều khiển: chưa có trên bản vẽ (minh họa)', 1);
  chap(t, '(7) CẢM BIẾN VÀ PHÒNG ĐIỀU KHIỂN');
  subs(t, [[0, 2, 'Đầu băng ống lồng có cảm biến – xem chậm từng loại'], [2, 6, 'Cảm biến (A) định vị thùng xe: đo tới vách bên và vách đầu thùng'],
           [6, 10, 'Cảm biến (B) kiểm tra từng bao đặt đúng ô'], [10, 13, 'Luôn có 1 người ở phòng điều khiển theo dõi kết quả cảm biến'],
           [13, 15.5, 'Cảm biến báo sai: bao đặt lệch khỏi ô'], [15.5, 18, 'Màn hình báo SAI – người điều khiển bấm DỪNG máy'],
           [18, D + 1, 'Bấm dừng: giả định KCP, cần Phon-Tech xác nhận cách xử lý']]);
}

function sBackup(t, D) {
  camKeys(t, [[0, [11.5, 6.5, 22.5], [6.7, 0.8, 16.0]], [7, [11.5, 6.5, 22.5], [6.7, 0.8, 15.5]], [9.5, [12.0, 7.5, 15.0], [6.7, 0.8, 10.0]], [D, [12.0, 7.5, 14.6], [6.7, 0.8, 9.6]]]);
  brushSpin(t);
  placeSlings([[POS.R1, 45], [POS.R0, 45], [POS.L1, 45], [POS.L2, 45]]);
  setRobot(V(BX - 1.3, 1.4, Z(760)), 0, [], true); setTele(TELE_X1 + 1.0, null);
  const slots = []; for (let r = 0; r <= 2; r++) for (let c = 2; c >= 0; c--) slots.push(V(ST_C.x + (r - 1) * 0.75, 0.15 + 0.03 + BH / 2 + 4 * BH, ST_C.z + (c - 1) * 0.5));
  let taken = 0; const P0 = V(BX, BAGY, Z(1048));
  const path = [P0, V(BX, BAGY, DROP_Z)].concat(OUT.slice(1));
  for (let i = 0; i < 9; i++) {
    const ta = 1.6 + i * 1.25; if (t < ta) break; taken = i + 1;
    const u = seg(t, ta, ta + 0.6);
    if (u < 1) { const p = slots[i].clone().lerp(P0, u); p.y += 0.5 * Math.sin(Math.PI * u); addBag(p, lerp(0, Math.PI / 2, u)); }
    else { const s = (t - ta - 0.6) * 1.3; if (s < pathLen(path)) { const [p, yaw] = pathAt(path, s); addBag(p, yaw); } }
  }
  slingBags(ST_C.x, 0.15, ST_C.z, 45 - taken, true);
  stWorker.userData.armL.rotation.z = Math.sin(t * 5) * 0.4;
  showLab('M', V(ST_C.x, 2.0, ST_C.z + 1.4), seg(t, 0.4, 0.8) * (1 - seg(t, 7, 7.4)));
  showLab('robx', V(BX - 1.3, 2.9, Z(760)), seg(t, 0.8, 1.2));
  showLab('via', V(BX + 0.2, 1.6, CZ), seg(t, 8.8, 9.2));
  card('M', 'Trạm xả tay dự phòng', ['1 công nhân xếp bao lên băng', 'bao đi thẳng qua cell vào băng tải ra', '~Phon-Tech xác nhận 04/11/2026'], seg(t, 1, 1.5) * (1 - seg(t, 7, 7.4)));
  chap(t, '(9) TRẠM XẢ TAY DỰ PHÒNG');
  subs(t, [[0, 1.6, 'Khi robot không hoạt động: dùng trạm xả tay dự phòng'], [1.6, 7.5, '1 công nhân lấy từng bao trên sling, đặt lên băng tải dự phòng'],
           [7.5, D + 1, 'Bao đi thẳng qua cell vào băng tải ra – vẫn xuất hàng được']]);
}

function sSummary(t, D) {
  camKeys(t, [[0, [6, 14, 30], [13, 0, 7]], [D, [16, 17, 33], [14, 0, 7]]]);
  defaultScene(t); brushSpin(t);
  const S = truckState(PLAN[3][1]); setTele(S.head.x - 0.6, S.head);
  setUI('panel', `<h2>Máy depal bao tự động – tóm tắt</h2>
    <div>• 2 băng con lăn sling, mỗi bên 2 sling, chạy luân phiên · <b>4 công nhân</b></div>
    <div>• Đầu hút chân không: <b>3 bao/lần</b>, thả lần lượt từng bao (chốt 05/11)</div>
    <div>• Công suất <b>40–45 tấn/giờ</b> = 800–900 bao/giờ · 1 xe 34 tấn ≈ <b>45–51 phút</b></div>
    <div>• Băng ống lồng vươn tối đa <b>18 m</b>, tự rải 5 bao × 9 lớp, có cảm biến · 1 người phòng điều khiển</div>
    <div>• Diện tích ≈ <b>262 m²</b> (ước tính) · điểm cao nhất băng tải <b>1,5 m</b></div>
    <div class="m">Minh họa 3D theo bản vẽ 20/10/2026 và Phon-Tech 04/11/2026. Cao độ từng băng tải, sàn xe, vị trí phòng điều khiển: giả định.</div>`, seg(t, 2.5, 3.2));
  chap(t, 'TÓM TẮT');
  subs(t, [[0, 2.5, 'Toàn bộ hệ thống: từ sling 45 bao tới thùng xe 34 tấn']]);
}

const FN = { overview: sOverview, area: sArea, flow: sFlow, pick: sPick, journey: sJourney, truck: sTruck, sensor: sSensor, backup: sBackup, summary: sSummary };
window.renderAt = (T) => {
  resetFrame();
  let name = SCN[SCN.length - 1][0];
  for (const [n] of SCN) { const [a, d] = SC[n]; if (T < a + d) { name = n; break; } }
  const [a, d] = SC[name];
  FN[name](T - a, d);
  if (CLEAN) for (const id in ui) ui[id].style.opacity = 0;
  bags.count = nb; bags.instanceMatrix.needsUpdate = true;
  renderer.render(scene, camera);
};
window.DUR = DUR;
window.ready = true;
