export interface FileEntry {
  path: string;
  name: string;
  pageCount: number;
  size?: number;
}

export interface TaskProgress {
  current: number;
  total: number;
  message: string;
}

export type SplitMode = 'range' | 'fixed' | 'extract' | 'bookmark';

export interface SplitOptions {
  ranges?: [number, number][];
  pagesPerFile?: number;
  pages?: number[];
  prefix?: string;
}

export interface ConvertOptions {
  pageSize?: 'A4' | 'Letter' | [number, number];
  orientation?: 'auto' | 'portrait' | 'landscape';
  margin?: number;
  quality?: number;
  fit?: 'contain' | 'cover' | 'stretch';
}

export interface EditOperation {
  type: 'replace' | 'add' | 'delete';
  page: number;
  search?: string;
  replace?: string;
  text?: string;
  position?: [number, number];
  font?: {
    family: string;
    size: number;
    color: string;
  };
}
