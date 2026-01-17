import { TrianglesDrawMode } from '../vendor/three.module.js';

// Minimal shim: GLTFLoader imports `toTrianglesDrawMode`.
// For typical GLTF files using triangle lists this is a no-op.
export function toTrianglesDrawMode( geometry, drawMode ) {
  // If already triangles or drawMode not provided, return geometry unchanged
  if ( drawMode === undefined || drawMode === TrianglesDrawMode ) {
    return geometry;
  }
  // Fallback: emit warning and return original geometry
  console.warn('toTrianglesDrawMode: conversion not implemented for drawMode', drawMode);
  return geometry;
}
