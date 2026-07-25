import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

export type CoreState = "idle" | "listening" | "thinking" | "responding";

const STATE_COLOR: Record<CoreState, string> = {
  idle: "#22d3ee",
  listening: "#3b82f6",
  thinking: "#a78bfa",
  responding: "#34e0a1",
};

const STATE_SPEED: Record<CoreState, number> = {
  idle: 0.15,
  listening: 0.35,
  thinking: 0.55,
  responding: 0.85,
};

// Wave displacement tuning per state — this is what makes the core
// visibly "fluctuate" (talk) rather than just pulse uniformly.
const WAVE_AMPLITUDE: Record<CoreState, number> = { idle: 0.02, listening: 0.05, thinking: 0.06, responding: 0.13 };
const WAVE_FREQUENCY: Record<CoreState, number> = { idle: 1.4, listening: 2.0, thinking: 3.2, responding: 2.4 };
const WAVE_TIME_SCALE: Record<CoreState, number> = { idle: 0.6, listening: 1.2, thinking: 2.2, responding: 1.8 };
const EMISSIVE_INTENSITY: Record<CoreState, number> = { idle: 1.1, listening: 1.35, thinking: 1.6, responding: 2 };
const LIGHT_INTENSITY: Record<CoreState, number> = { idle: 6, listening: 7.5, thinking: 9, responding: 12 };
const RING_COUNT = 16;

const VERTEX_SHADER = `
  uniform float uTime;
  uniform float uAmplitude;
  uniform float uFrequency;
  varying vec3 vNormal;
  varying vec3 vViewPosition;

  void main() {
    vNormal = normalize(normalMatrix * normal);

    float wave = sin(position.x * uFrequency + uTime)
               + sin(position.y * uFrequency * 1.3 + uTime * 1.15)
               + sin(position.z * uFrequency * 0.8 - uTime * 0.9);
    wave *= 0.333;

    vec3 displaced = position + normal * wave * uAmplitude;
    vec4 mvPosition = modelViewMatrix * vec4(displaced, 1.0);
    vViewPosition = -mvPosition.xyz;
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const FRAGMENT_SHADER = `
  uniform vec3 uColor;
  uniform float uGlow;
  varying vec3 vNormal;
  varying vec3 vViewPosition;

  void main() {
    vec3 viewDir = normalize(vViewPosition);
    float fresnel = pow(1.0 - max(dot(viewDir, normalize(vNormal)), 0.0), 2.5);
    vec3 color = uColor * (0.55 + fresnel * 1.9) * uGlow;
    gl_FragColor = vec4(color, 1.0);
  }
`;

function Core({ state }: { state: CoreState }) {
  const outerRef = useRef<THREE.Mesh>(null);
  const innerMatRef = useRef<THREE.ShaderMaterial>(null);
  const ringRef = useRef<THREE.Group>(null);
  const lightRef = useRef<THREE.PointLight>(null);
  const colorRef = useRef(new THREE.Color(STATE_COLOR.idle));
  const waveTimeRef = useRef(0);

  const targetColor = useMemo(() => new THREE.Color(STATE_COLOR[state]), [state]);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uAmplitude: { value: WAVE_AMPLITUDE.idle },
      uFrequency: { value: WAVE_FREQUENCY.idle },
      uColor: { value: new THREE.Color(STATE_COLOR.idle) },
      uGlow: { value: EMISSIVE_INTENSITY.idle },
    }),
    []
  );

  useFrame((_, delta) => {
    const speed = STATE_SPEED[state];

    if (outerRef.current) {
      outerRef.current.rotation.y += delta * speed;
      outerRef.current.rotation.x += delta * speed * 0.4;
    }
    if (ringRef.current) {
      ringRef.current.rotation.z += delta * speed * 0.6;
      ringRef.current.rotation.x = Math.PI / 2.4;
    }

    waveTimeRef.current += delta * WAVE_TIME_SCALE[state];
    colorRef.current.lerp(targetColor, delta * 3);

    if (innerMatRef.current) {
      const u = innerMatRef.current.uniforms;
      u.uTime.value = waveTimeRef.current;
      u.uAmplitude.value = THREE.MathUtils.lerp(u.uAmplitude.value, WAVE_AMPLITUDE[state], delta * 4);
      u.uFrequency.value = THREE.MathUtils.lerp(u.uFrequency.value, WAVE_FREQUENCY[state], delta * 4);
      u.uGlow.value = THREE.MathUtils.lerp(u.uGlow.value, EMISSIVE_INTENSITY[state], delta * 4);
      (u.uColor.value as THREE.Color).lerp(targetColor, delta * 3);
    }

    const outerMat = outerRef.current?.material as THREE.MeshBasicMaterial | undefined;
    if (outerMat) outerMat.color = colorRef.current;
    if (lightRef.current) {
      lightRef.current.color = colorRef.current;
      lightRef.current.intensity = LIGHT_INTENSITY[state];
    }
  });

  return (
    <group>
      <pointLight ref={lightRef} position={[0, 0, 0]} distance={6} decay={2} />
      <ambientLight intensity={0.15} />

      <mesh>
        <icosahedronGeometry args={[0.55, 4]} />
        <shaderMaterial
          ref={innerMatRef}
          uniforms={uniforms}
          vertexShader={VERTEX_SHADER}
          fragmentShader={FRAGMENT_SHADER}
          toneMapped={false}
        />
      </mesh>

      <mesh ref={outerRef}>
        <icosahedronGeometry args={[1, 1]} />
        <meshBasicMaterial wireframe transparent opacity={0.55} />
      </mesh>

      <group ref={ringRef}>
        {Array.from({ length: RING_COUNT }).map((_, i) => {
          const angle = (i / RING_COUNT) * Math.PI * 2;
          const radius = 1.5;
          return (
            <mesh key={i} position={[Math.cos(angle) * radius, Math.sin(angle) * radius, 0]}>
              <sphereGeometry args={[0.014, 6, 6]} />
              <meshBasicMaterial color={STATE_COLOR[state]} transparent opacity={0.7} />
            </mesh>
          );
        })}
      </group>
    </group>
  );
}

export default function AICore3D({ state }: { state: CoreState }) {
  return (
    <div className="h-32 w-32 sm:h-44 sm:w-44 lg:h-56 lg:w-56">
      <Canvas camera={{ position: [0, 0, 3.2], fov: 45 }} gl={{ alpha: true, antialias: true }}>
        <Core state={state} />
      </Canvas>
    </div>
  );
}
