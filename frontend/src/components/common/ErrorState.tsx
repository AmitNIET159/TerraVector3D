interface Props { title?: string; message?: string; }

export default function ErrorState({ title = 'Error', message = 'Something went wrong.' }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-2 text-center px-4">
      <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center text-lg">⚠️</div>
      <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      <p className="text-xs text-gray-500">{message}</p>
    </div>
  );
}
