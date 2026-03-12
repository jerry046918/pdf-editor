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

// 批量分拆相关类型
export interface BatchFile {
  path: string;
  name: string;
  pageCount: number;
}

export interface BatchSplitResult {
  file: string;
  success: boolean;
  output_files?: string[];
  error?: string;
}

export interface BatchSplitResponse {
  success: boolean;
  error?: string;
  results: BatchSplitResult[];
  total_files: number;
  success_count: number;
  failed_count: number;
}
