export const validateFile = (file: File): string | null => {
  // Check file type
  if (file.type !== 'application/pdf') {
    return 'Please upload a PDF file only.';
  }
  
  // Check file size (10MB = 10 * 1024 * 1024 bytes)
  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    return 'File size must be less than 10MB.';
  }
  
  return null;
};

export const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
};


