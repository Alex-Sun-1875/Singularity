//! CPU kernel v3: A*, collision/visibility, connectors and route simplification.
//! Cached A* heuristic lengths and host Math.hypot for query distances preserve
//! TypeScript results without per-sample JS collision callbacks.
//! Indexed heap sift operations follow the project's TinyQueue adaptation (ISC,
//! Vladimir Agafonkin; see build-templates/web-desktop/THIRD_PARTY_NOTICES.txt).
use std::ptr;

#[link(wasm_import_module = "navigation")]
extern "C" {
    fn hypot(x: f64, z: f64) -> f64;
}

const CONTEXT_LIMIT: usize = 4;
#[repr(C)]
#[derive(Clone, Copy, Default)]
struct Rect { x: f64, z: f64, width: f64, depth: f64 }

struct Obstacles {
    width: f64, depth: f64, rectangles: Vec<Rect>,
    min_x: i32, min_z: i32, columns: usize, rows: usize,
    offsets: Vec<u32>, indices: Vec<usize>, large: Vec<usize>,
}
impl Obstacles {
    fn new(width: f64, depth: f64, count: usize) -> Self {
        let min_x=(-width/8.).floor() as i32; let min_z=(-depth/8.).floor() as i32;
        let columns=((width/8.).floor() as i32-min_x+1) as usize;
        let rows=((depth/8.).floor() as i32-min_z+1) as usize;
        Self {width,depth,rectangles:vec![Rect::default();count],min_x,min_z,columns,rows,
            offsets:Vec::new(),indices:Vec::new(),large:Vec::new()}
    }
    fn prepare(&mut self) {
        if self.rectangles.len()<8 { return; }
        let mut counts=vec![0u32;self.columns*self.rows];
        let mut spans=Vec::with_capacity(self.rectangles.len());
        for (i,o) in self.rectangles.iter().enumerate() {
            let left=((o.x-o.width/2.)/4.).floor().max(self.min_x as f64) as i32;
            let right=((o.x+o.width/2.)/4.).floor().min((self.min_x+self.columns as i32-1) as f64) as i32;
            let bottom=((o.z-o.depth/2.)/4.).floor().max(self.min_z as f64) as i32;
            let top=((o.z+o.depth/2.)/4.).floor().min((self.min_z+self.rows as i32-1) as f64) as i32;
            if left>right || bottom>top || (right-left+1)*(top-bottom+1)>64 {
                self.large.push(i); spans.push(None); continue;
            }
            for z in bottom..=top { for x in left..=right {
                counts[(z-self.min_z) as usize*self.columns+(x-self.min_x) as usize]+=1;
            }}
            spans.push(Some((left,right,bottom,top)));
        }
        self.offsets=Vec::with_capacity(counts.len()+1); self.offsets.push(0);
        for n in counts { self.offsets.push(self.offsets.last().unwrap()+n); }
        self.indices=vec![0;*self.offsets.last().unwrap() as usize];
        let mut cursor=self.offsets.clone();
        for (i,span) in spans.into_iter().enumerate() {
            if let Some((left,right,bottom,top))=span { for z in bottom..=top { for x in left..=right {
                let cell=(z-self.min_z) as usize*self.columns+(x-self.min_x) as usize;
                self.indices[cursor[cell] as usize]=i; cursor[cell]+=1;
            }}}
        }
    }
    #[inline]
    fn hits(&self,index:usize,x:f64,z:f64,r:f64) -> bool {
        let o=&self.rectangles[index];
        (x-o.x).abs()<o.width/2.+r && (z-o.z).abs()<o.depth/2.+r
    }
    #[inline]
    fn blocked(&self,x:f64,z:f64,r:f64) -> bool {
        if x.abs()>self.width/2.-r || z.abs()>self.depth/2.-r { return true; }
        if self.rectangles.len()<8 { return (0..self.rectangles.len()).any(|i|self.hits(i,x,z,r)); }
        if self.large.iter().any(|&i|self.hits(i,x,z,r)) { return true; }
        let min_x=((x-r)/4.).floor() as i32; let max_x=((x+r)/4.).floor() as i32;
        let min_z=((z-r)/4.).floor() as i32; let max_z=((z+r)/4.).floor() as i32;
        for cz in min_z..=max_z { for cx in min_x..=max_x {
            if cx<self.min_x || cz<self.min_z || cx>=self.min_x+self.columns as i32 || cz>=self.min_z+self.rows as i32 { continue; }
            let cell=(cz-self.min_z) as usize*self.columns+(cx-self.min_x) as usize;
            for at in self.offsets[cell]..self.offsets[cell+1] {
                if self.hits(self.indices[at as usize],x,z,r) { return true; }
            }
        }}
        false
    }
    unsafe fn visible(&self,a:Point,b:Point,r:f64) -> bool {
        let steps=(hypot(b.x-a.x,b.z-a.z)/0.18).ceil().max(1.) as usize;
        for i in 0..=steps {
            let t=i as f64/steps as f64;
            if self.blocked(a.x+(b.x-a.x)*t,a.z+(b.z-a.z)*t,r) { return false; }
        }
        true
    }
    fn edge(&self,x:i32,z:i32,dx:i32,dz:i32,direction:usize) -> bool {
        if self.blocked((x+dx) as f64,(z+dz) as f64,0.42) { return false; }
        // Exactly ceil(hypot(dx,dz)/.18) for the existing eight unit edges.
        let steps=if direction<4 {6} else {8};
        for i in 0..=steps {
            let t=i as f64/steps as f64;
            if self.blocked(x as f64+dx as f64*t,z as f64+dz as f64*t,0.42) { return false; }
        }
        true
    }
}

#[repr(C)]
#[derive(Clone, Copy, Default)]
struct Point {x:f64,z:f64}
struct Search {
    columns: usize,
    rows: usize,
    generation: u32,
    edges: Vec<u16>,
    seen: Vec<u32>,
    closed: Vec<u8>,
    cost: Vec<f64>,
    score: Vec<f64>,
    previous: Vec<i32>,
    order: Vec<u32>,
    position: Vec<usize>,
    heap: Vec<usize>,
    route: Vec<i32>,
    lengths: Vec<f64>,
    obstacles: Obstacles,
    input: Vec<Point>, output: Vec<Point>, visibility: Vec<u8>,
}
static mut CONTEXTS: [*mut Search;CONTEXT_LIMIT] = [ptr::null_mut();CONTEXT_LIMIT];

impl Search {
    fn new(width:f64,depth:f64,count_obstacles:usize) -> Self {
        let columns=(width/2.).floor() as usize*2+1;
        let rows=(depth/2.).floor() as usize*2+1;
        let count = columns * rows;
        Self { columns, rows, generation: 0, edges: vec![0; count],
            seen: vec![0; count], closed: vec![0; count], cost: vec![0.; count],
            score: vec![0.; count], previous: vec![-1; count], order: vec![0; count],
            position: vec![0; count], heap: Vec::with_capacity(count),
            route: Vec::with_capacity(count), lengths:vec![f64::NAN;count],
            obstacles:Obstacles::new(width,depth,count_obstacles),
            input:Vec::new(),output:Vec::new(),visibility:Vec::new() }
    }
    unsafe fn length(&mut self,x:i32,z:i32) -> f64 {
        let x=x.unsigned_abs() as usize; let z=z.unsigned_abs() as usize;
        let at=z*self.columns+x;
        if self.lengths[at].is_nan() { self.lengths[at]=hypot(x as f64,z as f64); }
        self.lengths[at]
    }
    fn before(&self, a: usize, b: usize) -> bool {
        self.score[a] < self.score[b] || self.score[a] == self.score[b] && self.order[a] < self.order[b]
    }
    fn up(&mut self, mut pos: usize) {
        let node = self.heap[pos];
        while pos > 0 {
            let parent = (pos - 1) >> 1;
            let current = self.heap[parent];
            if !self.before(node, current) { break; }
            self.heap[pos] = current; self.position[current] = pos; pos = parent;
        }
        self.heap[pos] = node; self.position[node] = pos;
    }
    fn pop(&mut self) -> usize {
        let top = self.heap[0];
        let bottom = self.heap.pop().unwrap();
        let half = self.heap.len() >> 1;
        if !self.heap.is_empty() {
            let mut pos = 0;
            while pos < half {
                let mut child = (pos << 1) + 1;
                let right = child + 1;
                if right < self.heap.len() && self.before(self.heap[right], self.heap[child]) { child = right; }
                if !self.before(self.heap[child], bottom) { break; }
                self.heap[pos] = self.heap[child]; self.position[self.heap[pos]] = pos; pos = child;
            }
            self.heap[pos] = bottom; self.position[bottom] = pos;
        }
        top
    }
    unsafe fn search(&mut self, start: usize, end: usize) -> usize {
        self.heap.clear(); self.route.clear();
        self.generation = self.generation.wrapping_add(1);
        if self.generation == 0 { self.seen.fill(0); self.generation = 1; }
        let generation = self.generation;
        let ex = (end % self.columns) as f64;
        let ez = (end / self.columns) as f64;
        self.seen[start] = generation; self.closed[start] = 0; self.cost[start] = 0.;
        self.score[start] = self.length((start % self.columns) as i32-ex as i32,(start / self.columns) as i32-ez as i32);
        self.order[start] = 0; self.position[start] = 0; self.heap.push(start);
        let mut order = 1;
        const DX: [i32; 8] = [1, -1, 0, 0, 1, 1, -1, -1];
        const DZ: [i32; 8] = [0, 0, 1, -1, 1, -1, 1, -1];
        for _ in 0..20_000 {
            if self.heap.is_empty() { break; }
            let current = self.pop();
            if current == end {
                let mut node = end;
                while node != start { self.route.push(node as i32); node = self.previous[node] as usize; }
                self.route.push(start as i32); self.route.reverse(); return self.route.len();
            }
            self.closed[current] = 1;
            let cx = (current % self.columns) as i32;
            let cz = (current / self.columns) as i32;
            for direction in 0..8 {
                let nx = cx + DX[direction]; let nz = cz + DZ[direction];
                if nx < 0 || nz < 0 || nx >= self.columns as i32 || nz >= self.rows as i32 { continue; }
                let next = nz as usize * self.columns + nx as usize;
                let known_node = self.seen[next] == generation;
                if known_node && self.closed[next] != 0 { continue; }
                let known = 1u16 << (direction + 8); let bit = 1u16 << direction;
                let mut mask = self.edges[current];
                if mask & known == 0 {
                    let hw = (self.columns / 2) as i32; let hd = (self.rows / 2) as i32;
                    if self.obstacles.edge(cx-hw,cz-hd,DX[direction],DZ[direction],direction) { mask |= bit; }
                    mask |= known; self.edges[current] = mask;
                }
                if mask & bit == 0 { continue; }
                let cost = self.cost[current] + if direction < 4 { 1. } else { std::f64::consts::SQRT_2 };
                if known_node && cost >= self.cost[next] { continue; }
                self.cost[next] = cost;
                self.score[next] = cost + self.length(nx-ex as i32,nz-ez as i32);
                self.previous[next] = current as i32;
                if known_node { self.up(self.position[next]); }
                else {
                    self.seen[next] = generation; self.closed[next] = 0;
                    self.order[next] = order; order += 1;
                    let pos = self.heap.len(); self.heap.push(next); self.up(pos);
                }
            }
        }
        0
    }
}

#[no_mangle]
pub extern "C" fn api_version() -> u32 { 3 }
#[no_mangle]
pub unsafe extern "C" fn create_context(slot:usize,width:f64,depth:f64,count:usize) {
    clear_context(slot);
    CONTEXTS[slot]=Box::into_raw(Box::new(Search::new(width,depth,count)));
}
#[no_mangle]
pub unsafe extern "C" fn obstacles_pointer(slot:usize) -> *mut f64 { (*CONTEXTS[slot]).obstacles.rectangles.as_mut_ptr() as *mut f64 }
#[no_mangle]
pub unsafe extern "C" fn prepare_context(slot:usize) { (*CONTEXTS[slot]).obstacles.prepare(); }
#[no_mangle]
pub unsafe extern "C" fn route_pointer(slot:usize) -> *const i32 { (*CONTEXTS[slot]).route.as_ptr() }
#[no_mangle]
pub unsafe extern "C" fn search_context(slot:usize,start:usize,end:usize) -> usize { (*CONTEXTS[slot]).search(start,end) }
#[no_mangle]
pub unsafe extern "C" fn clear_context(slot:usize) {
    let old=CONTEXTS[slot]; CONTEXTS[slot]=ptr::null_mut();
    if !old.is_null() { drop(Box::from_raw(old)); }
}

// Scratch buffers are context-owned and bounded by the validated map/query limits.
#[no_mangle]
pub unsafe extern "C" fn input_pointer(slot:usize,count:usize) -> *mut f64 {
    let s=&mut *CONTEXTS[slot];s.input.resize(count,Point::default());s.input.as_mut_ptr() as *mut f64
}
#[no_mangle]
pub unsafe extern "C" fn points_pointer(slot:usize) -> *const f64 { (*CONTEXTS[slot]).output.as_ptr() as *const f64 }
#[no_mangle]
pub unsafe extern "C" fn visible_context(slot:usize,ax:f64,az:f64,bx:f64,bz:f64,r:f64) -> u32 {
    (*CONTEXTS[slot]).obstacles.visible(Point{x:ax,z:az},Point{x:bx,z:bz},r) as u32
}
#[no_mangle]
pub unsafe extern "C" fn visibility_pointer(slot:usize) -> *const u8 { (*CONTEXTS[slot]).visibility.as_ptr() }
#[no_mangle]
pub unsafe extern "C" fn visibility_context(slot:usize,x:f64,z:f64,count:usize,r:f64) {
    let s=&mut *CONTEXTS[slot];s.visibility.clear();
    for p in s.input.iter().take(count) {s.visibility.push(s.obstacles.visible(Point{x,z},*p,r) as u8);}
}
#[no_mangle]
pub unsafe extern "C" fn connector_context(slot:usize,x:f64,z:f64) -> usize {
    // ECMAScript Math.round: ties go towards +infinity, including negatives.
    let round=|v:f64| {let n=v.floor();if v-n<0.5 {n} else {n+1.}};
    let s=&mut *CONTEXTS[slot];s.output.clear();let p=Point{x,z};
    let mut candidates=[(0.,Point::default());49];let mut i=0;
    for dx in -3..=3 { for dz in -3..=3 {
        let q=Point{x:round(x)+dx as f64,z:round(z)+dz as f64};
        candidates[i]=(hypot(q.x-x,q.z-z),q);i+=1;
    }}
    // Stable order matches JS Array.sort and the original x-then-z enumeration.
    candidates.sort_by(|a,b|a.0.partial_cmp(&b.0).unwrap());
    for (_,q) in candidates { if !s.obstacles.blocked(q.x,q.z,0.42) && s.obstacles.visible(p,q,0.32) {s.output.push(q);break;} }
    s.output.len()
}
#[no_mangle]
pub unsafe extern "C" fn simplify_context(slot:usize,count:usize) -> usize {
    let s=&mut *CONTEXTS[slot];s.route.clear();if count==0 {return 0;}
    // Return original indices so JavaScript retains endpoint/object metadata.
    s.route.push(0);let mut i=0;
    while i<count-1 {
        let mut next=i+1;
        for j in i+2..count {if !s.obstacles.visible(s.input[i],s.input[j],0.42) {break;}next=j;}
        s.route.push(next as i32);i=next;
    }
    s.route.len()
}
