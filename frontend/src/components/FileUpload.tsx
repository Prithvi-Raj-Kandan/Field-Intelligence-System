import { useRef, type ChangeEvent } from "react";
import "./FileUpload.css";

interface FileUploadProps {
  label: string;
  hint?: string;
  accept: string;
  multiple?: boolean;
  files: File[];
  onChange: (files: File[]) => void;
  previews?: boolean;
}

export function FileUpload({
  label,
  hint,
  accept,
  multiple = false,
  files,
  onChange,
  previews = true,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? []);
    onChange(multiple ? [...files, ...selected] : selected.slice(0, 1));
    e.target.value = "";
  };

  const remove = (index: number) => {
    onChange(files.filter((_, i) => i !== index));
  };

  return (
    <div className="file-upload">
      <span className="file-upload__label">{label}</span>
      {hint ? <span className="file-upload__hint">{hint}</span> : null}
      <button type="button" className="file-upload__btn" onClick={() => inputRef.current?.click()}>
        + Add {multiple ? "files" : "file"}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        hidden
        onChange={handleChange}
      />
      {files.length > 0 ? (
        <ul className="file-upload__list">
          {files.map((file, i) => (
            <li key={`${file.name}-${i}`} className="file-upload__item">
              {previews && file.type.startsWith("image/") ? (
                <img src={URL.createObjectURL(file)} alt="" className="file-upload__thumb" />
              ) : (
                <span className="file-upload__name">{file.name}</span>
              )}
              <button type="button" className="file-upload__remove" onClick={() => remove(i)} aria-label="Remove">
                ×
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
