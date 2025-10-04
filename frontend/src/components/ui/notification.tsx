import React, { useEffect } from 'react';
import { CheckCircle, XCircle, Info, Loader2 } from 'lucide-react';

interface NotificationProps {
  message: string;
  type: 'success' | 'error' | 'info' | 'loading';
  onClose: () => void;
  duration?: number;
}

export const Notification: React.FC<NotificationProps> = ({
  message,
  type,
  onClose,
  duration = 3000
}) => {
  useEffect(() => {
    if (type !== 'loading' && duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [type, duration, onClose]);

  const config = {
    success: {
      icon: CheckCircle,
      bgColor: 'bg-green-500',
      textColor: 'text-white',
      borderColor: 'border-green-600'
    },
    error: {
      icon: XCircle,
      bgColor: 'bg-red-500',
      textColor: 'text-white',
      borderColor: 'border-red-600'
    },
    info: {
      icon: Info,
      bgColor: 'bg-blue-500',
      textColor: 'text-white',
      borderColor: 'border-blue-600'
    },
    loading: {
      icon: Loader2,
      bgColor: 'bg-yellow-500',
      textColor: 'text-white',
      borderColor: 'border-yellow-600'
    }
  };

  const { icon: Icon, bgColor, textColor, borderColor } = config[type];

  return (
    <div
      className={`flex items-center gap-3 px-6 py-4 rounded-lg shadow-2xl border-2 ${bgColor} ${textColor} ${borderColor} min-w-[320px] max-w-md animate-slide-up`}
    >
      <Icon
        size={24}
        className={type === 'loading' ? 'animate-spin' : ''}
      />
      <span className="font-semibold text-sm flex-1">{message}</span>
      {type !== 'loading' && (
        <button
          onClick={onClose}
          className="hover:opacity-70 transition-opacity ml-2"
        >
          <XCircle size={20} />
        </button>
      )}
    </div>
  );
};
