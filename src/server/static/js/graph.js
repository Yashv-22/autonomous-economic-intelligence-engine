/**
 * Interactive Knowledge Graph Canvas Controller
 * Multi-Entity Force-Directed Visualization
 */

class KnowledgeGraphVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        
        this.nodes = [];
        this.edges = [];
        this.nodeMap = new Map();
        
        this.scale = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        
        this.selectedNode = null;
        this.hoveredNode = null;
        
        this.initCanvasSize();
        this.bindEvents();
    }

    initCanvasSize() {
        if (!this.canvas) return;
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width || 800;
        this.canvas.height = rect.height || 600;
        this.panX = this.canvas.width / 2;
        this.panY = this.canvas.height / 2;
    }

    bindEvents() {
        if (!this.canvas) return;

        window.addEventListener('resize', () => {
            this.initCanvasSize();
            this.render();
        });

        this.canvas.addEventListener('mousedown', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            // Check if clicked a node
            const clicked = this.findNodeAt(mouseX, mouseY);
            if (clicked) {
                this.selectedNode = clicked;
                if (window.onGraphNodeSelected) {
                    window.onGraphNodeSelected(clicked);
                }
                this.render();
            } else {
                this.isDragging = true;
                this.dragStartX = mouseX - this.panX;
                this.dragStartY = mouseY - this.panY;
            }
        });

        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            if (this.isDragging) {
                this.panX = mouseX - this.dragStartX;
                this.panY = mouseY - this.dragStartY;
                this.render();
            } else {
                const hovered = this.findNodeAt(mouseX, mouseY);
                if (hovered !== this.hoveredNode) {
                    this.hoveredNode = hovered;
                    this.canvas.style.cursor = hovered ? 'pointer' : 'grab';
                    this.render();
                }
            }
        });

        this.canvas.addEventListener('mouseup', () => {
            this.isDragging = false;
        });

        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
            this.scale = Math.max(0.2, Math.min(3.0, this.scale * zoomFactor));
            this.render();
        }, { passive: false });
    }

    setData(nodes, edges) {
        this.nodeMap.clear();
        this.nodes = [];
        this.edges = [];

        // Position nodes in concentric rings / clusters
        const total = nodes.length;
        const radiusStep = 180;
        
        nodes.forEach((n, idx) => {
            const angle = (idx / Math.max(1, total)) * 2 * Math.PI;
            const ring = 1 + (idx % 3);
            const dist = ring * (radiusStep / 2) + ((idx * 17) % 60);
            
            const nodeObj = {
                id: n.id || `node-${idx}`,
                label: n.label || n.name || n.title || n.id,
                type: n.type || n.category || 'ENTITY',
                x: Math.cos(angle) * dist,
                y: Math.sin(angle) * dist,
                vx: 0,
                vy: 0,
                radius: this.getNodeRadius(n.type),
                color: this.getNodeColor(n.type),
                raw: n
            };
            this.nodes.push(nodeObj);
            this.nodeMap.set(nodeObj.id, nodeObj);
        });

        edges.forEach((e) => {
            const src = this.nodeMap.get(e.source);
            const tgt = this.nodeMap.get(e.target);
            if (src && tgt) {
                this.edges.push({
                    source: src,
                    target: tgt,
                    relation: e.relation || e.type || 'relates_to'
                });
            }
        });

        // Run brief layout relaxation
        this.relaxSimulation(40);
        this.render();
    }

    getNodeRadius(type) {
        switch ((type || '').toUpperCase()) {
            case 'OPPORTUNITY':
            case 'SOLUTION': return 18;
            case 'PROBLEM':
            case 'CONTRADICTION': return 15;
            case 'CLAIM': return 12;
            default: return 10;
        }
    }

    getNodeColor(type) {
        switch ((type || '').toUpperCase()) {
            case 'OPPORTUNITY':
            case 'SOLUTION': return '#047857'; // Emerald
            case 'PROBLEM': return '#b91c1c';    // Crimson
            case 'CONTRADICTION': return '#b45309'; // Amber
            case 'CLAIM': return '#1d4ed8';      // Blue
            case 'METRIC': return '#6d28d9';     // Purple
            default: return '#0f2744';          // Navy
        }
    }

    relaxSimulation(iterations) {
        const k = 120; // ideal spring length
        for (let it = 0; it < iterations; it++) {
            // Repulsion between all nodes
            for (let i = 0; i < this.nodes.length; i++) {
                for (let j = i + 1; j < this.nodes.length; j++) {
                    const n1 = this.nodes[i];
                    const n2 = this.nodes[j];
                    const dx = n2.x - n1.x;
                    const dy = n2.y - n1.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                    if (dist < 300) {
                        const force = (k * k) / dist;
                        const fx = (dx / dist) * force * 0.05;
                        const fy = (dy / dist) * force * 0.05;
                        n1.x -= fx;
                        n1.y -= fy;
                        n2.x += fx;
                        n2.y += fy;
                    }
                }
            }

            // Spring attraction along edges
            for (const edge of this.edges) {
                const dx = edge.target.x - edge.source.x;
                const dy = edge.target.y - edge.source.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = (dist - k) * 0.04;
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;
                edge.source.x += fx;
                edge.source.y += fy;
                edge.target.x -= fx;
                edge.target.y -= fy;
            }
        }
    }

    findNodeAt(screenX, screenY) {
        for (let i = this.nodes.length - 1; i >= 0; i--) {
            const n = this.nodes[i];
            const nodeScreenX = this.panX + n.x * this.scale;
            const nodeScreenY = this.panY + n.y * this.scale;
            const r = (n.radius + 4) * this.scale;
            const dx = screenX - nodeScreenX;
            const dy = screenY - nodeScreenY;
            if (dx * dx + dy * dy <= r * r) {
                return n;
            }
        }
        return null;
    }

    resetView() {
        this.scale = 1.0;
        this.panX = this.canvas.width / 2;
        this.panY = this.canvas.height / 2;
        this.selectedNode = null;
        this.render();
    }

    render() {
        if (!this.ctx || !this.canvas) return;
        const ctx = this.ctx;
        
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw grid
        ctx.save();
        ctx.strokeStyle = '#f1f5f9';
        ctx.lineWidth = 1;
        const gridSize = 40 * this.scale;
        const offsetX = this.panX % gridSize;
        const offsetY = this.panY % gridSize;
        
        ctx.beginPath();
        for (let x = offsetX; x < this.canvas.width; x += gridSize) {
            ctx.moveTo(x, 0);
            ctx.lineTo(x, this.canvas.height);
        }
        for (let y = offsetY; y < this.canvas.height; y += gridSize) {
            ctx.moveTo(0, y);
            ctx.lineTo(this.canvas.width, y);
        }
        ctx.stroke();
        ctx.restore();

        // Draw edges
        ctx.save();
        for (const edge of this.edges) {
            const x1 = this.panX + edge.source.x * this.scale;
            const y1 = this.panY + edge.source.y * this.scale;
            const x2 = this.panX + edge.target.x * this.scale;
            const y2 = this.panY + edge.target.y * this.scale;

            ctx.strokeStyle = '#cbd5e1';
            ctx.lineWidth = 1.2 * this.scale;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }
        ctx.restore();

        // Draw nodes
        ctx.save();
        for (const node of this.nodes) {
            const sx = this.panX + node.x * this.scale;
            const sy = this.panY + node.y * this.scale;
            const r = node.radius * this.scale;

            // Circle fill
            ctx.beginPath();
            ctx.arc(sx, sy, r, 0, 2 * Math.PI);
            ctx.fillStyle = node.color;
            ctx.fill();

            // Border / glow if selected
            if (this.selectedNode === node) {
                ctx.strokeStyle = '#0f172a';
                ctx.lineWidth = 3 * this.scale;
                ctx.stroke();
            } else if (this.hoveredNode === node) {
                ctx.strokeStyle = '#94a3b8';
                ctx.lineWidth = 2 * this.scale;
                ctx.stroke();
            }

            // Text label
            ctx.font = `${Math.max(10, Math.round(11 * this.scale))}px Inter, sans-serif`;
            ctx.fillStyle = '#0f172a';
            ctx.textAlign = 'center';
            const label = node.label.length > 24 ? node.label.substring(0, 22) + '...' : node.label;
            ctx.fillText(label, sx, sy + r + 14 * this.scale);
        }
        ctx.restore();
    }
}

window.KnowledgeGraphVisualizer = KnowledgeGraphVisualizer;
