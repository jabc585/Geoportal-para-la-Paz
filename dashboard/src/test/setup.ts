import "@testing-library/jest-dom/vitest";

// jsdom no implementa ResizeObserver y el ResponsiveContainer de recharts lo
// usa al montar: sin este doble, el árbol de React revienta en cada test.
if (!("ResizeObserver" in globalThis)) {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
}

if (!("matchMedia" in globalThis)) {
  globalThis.matchMedia = ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener() {},
    removeEventListener() {},
    addListener() {},
    removeListener() {},
    dispatchEvent: () => false,
  })) as unknown as typeof matchMedia;
}
