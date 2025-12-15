import { formatFileSize } from '@/lib/utils';
import type { ResumeInfo } from '@/types';

interface ResumeUploadProps {
  uploadedFile: File | null;
  isDragging: boolean;
  uploadError: string | null;
  isUploading?: boolean;
  cvData?: ResumeInfo | null;
  needsClarification?: boolean;
  clarificationQuestions?: string[] | null;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onFileInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onClickUpload: () => void;
  onRemoveFile: () => void;
}

export const ResumeUpload = ({
  uploadedFile,
  isDragging,
  uploadError,
  isUploading = false,
  cvData,
  needsClarification = false,
  clarificationQuestions,
  fileInputRef,
  onDragOver,
  onDragLeave,
  onDrop,
  onFileInputChange,
  onClickUpload,
  onRemoveFile,
}: ResumeUploadProps) => {
  return (
    <div>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={onFileInputChange}
        className="hidden"
      />
      
      {/* PDF Upload Area */}
      {!uploadedFile ? (
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={onClickUpload}
          className={`flex min-h-[200px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-all ${
            isDragging
              ? 'border-indigo-500 bg-indigo-50 dark:border-indigo-400 dark:bg-indigo-950/30'
              : 'border-slate-300 bg-slate-50/50 hover:border-indigo-400 hover:bg-indigo-50/30 dark:border-slate-600 dark:bg-slate-800/30 dark:hover:border-indigo-500 dark:hover:bg-indigo-950/20'
          }`}
        >
          <div className="mb-4">
            <svg
              className={`mx-auto h-16 w-16 transition-colors ${
                isDragging
                  ? 'text-indigo-600 dark:text-indigo-400'
                  : 'text-slate-400 dark:text-slate-500'
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          <p className="mb-2 text-base font-medium text-slate-700 dark:text-slate-300">
            {isDragging ? 'Drop your PDF here' : 'Drag and drop your resume'}
          </p>
          <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">or</p>
          <button className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600">
            Choose File
          </button>
          <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
            PDF only, max 10MB
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/50">
          <div className="flex items-start gap-3">
            <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-900/50">
              <svg
                className="h-7 w-7 text-indigo-600 dark:text-indigo-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium text-slate-900 dark:text-slate-100">
                {uploadedFile.name}
              </p>
              <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                {formatFileSize(uploadedFile.size)}
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemoveFile();
              }}
              className="flex-shrink-0 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-300"
              aria-label="Remove file"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      )}
      
      {/* Upload Progress */}
      {isUploading && (
        <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/50 dark:bg-blue-950/30">
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent dark:border-blue-400"></div>
            <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
              Processing your resume...
            </p>
          </div>
        </div>
      )}

      {/* Success Message */}
      {cvData && !isUploading && (
        <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900/50 dark:bg-green-950/30">
          <div className="flex items-start gap-3">
            <svg
              className="h-5 w-5 flex-shrink-0 text-green-600 dark:text-green-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <p className="font-medium text-green-700 dark:text-green-300">
                Resume processed successfully!
              </p>
              <p className="mt-0.5 text-sm text-green-600 dark:text-green-400">
                Found: {cvData.name}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Clarification Needed */}
      {needsClarification && clarificationQuestions && !isUploading && (
        <div className="mt-4 rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900/50 dark:bg-yellow-950/30">
          <div className="flex items-start gap-3">
            <svg
              className="h-5 w-5 flex-shrink-0 text-yellow-600 dark:text-yellow-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <p className="font-medium text-yellow-700 dark:text-yellow-300">
                Additional information needed
              </p>
              <p className="mt-0.5 text-sm text-yellow-600 dark:text-yellow-400">
                Please answer questions in the chat to complete your profile.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {uploadError && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/30">
          <div className="flex items-start gap-3">
            <svg
              className="h-5 w-5 flex-shrink-0 text-red-600 dark:text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-sm font-medium text-red-700 dark:text-red-400">{uploadError}</p>
          </div>
        </div>
      )}
    </div>
  );
};

