// 文件名: mathjax-react.d.ts

declare module 'mathjax-react' {
  import React from 'react';

  export interface MathJaxContextProps {
    config?: object;
    children: React.ReactNode;
    onLoad?: () => void;
    onError?: (error: any) => void;
  }

  const MathJaxContext: React.FC<MathJaxContextProps>;
  export default MathJaxContext;

  export interface MathJaxProps {
    formula: string;
    inline?: boolean;
    hideUntilTypeset?: "first" | "every";
    children?: React.ReactNode;
    onRender?: () => void;
  }
  
  export const MathJax: React.FC<MathJaxProps>;
}