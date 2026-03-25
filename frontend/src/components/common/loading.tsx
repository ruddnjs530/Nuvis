import Spinner from './spinner';

export default function Loading() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center p-10">
      <Spinner className="shadow-sm" />
    </div>
  );
}
