import React, { ReactNode } from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
  children?: ReactNode;
  className?: string;
}

export function Button({
  asChild,
  className = '',
  children,
  ...props
}: ButtonProps) {
  const baseStyles = 'inline-flex items-center justify-center px-4 py-2 rounded font-medium transition-colors focus:outline-none';
  const combinedClassName = `${baseStyles} ${className}`;

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      ...props,
      className: combinedClassName,
    } as any);
  }

  return (
    <button className={combinedClassName} {...props}>
      {children}
    </button>
  );
}
