/// <reference types="nativewind/types" />

declare module '*.module.css' {
  const content: Record<string, string>;
  export default content;
}

declare module '@/global.css';

declare module '*.css';
