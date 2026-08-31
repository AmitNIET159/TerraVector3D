type Status = 'valid' | 'pending' | 'warning' | 'invalid' | 'conflict';

const STYLES: Record<Status, string> = {
  valid: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  pending: 'bg-gray-100 text-gray-500 border-gray-200',
  warning: 'bg-amber-50 text-amber-700 border-amber-200',
  invalid: 'bg-red-50 text-red-700 border-red-200',
  conflict: 'bg-red-100 text-red-800 border-red-300',
};

const LABELS: Record<Status, string> = {
  valid: 'VALID', pending: 'PENDING', warning: 'NEEDS REVIEW', invalid: 'INVALID', conflict: 'CONFLICT',
};

interface Props { status: Status; label?: string; }

export default function StatusBadge({ status, label }: Props) {
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${STYLES[status]}`}>
      {label || LABELS[status]}
    </span>
  );
}
