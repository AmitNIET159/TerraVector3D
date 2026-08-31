interface Props { icon?: string; message?: string; }

export default function EmptyState({ icon = '📋', message = 'No data available.' }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-2 text-center px-4 py-8">
      <span className="text-2xl opacity-40">{icon}</span>
      <p className="text-xs text-gray-400">{message}</p>
    </div>
  );
}
