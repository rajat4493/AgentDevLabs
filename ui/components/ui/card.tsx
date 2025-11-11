import * as React from "react";
import { cn } from "@/lib/utils";

type DivProps = React.HTMLAttributes<HTMLDivElement>;

export function Card({ className, ...props }: DivProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-gray-200 bg-white shadow-sm",
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: DivProps) {
  return (
    <div className={cn("p-4 sm:p-5 border-b border-gray-100", className)} {...props} />
  );
}

export function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-lg font-semibold", className)} {...props} />;
}

export function CardDescription({ className, ...props }: DivProps) {
  return (
    <div className={cn("text-sm text-gray-600", className)} {...props} />
  );
}

export function CardContent({ className, ...props }: DivProps) {
  return <div className={cn("p-4 sm:p-5", className)} {...props} />;
}

export function CardFooter({ className, ...props }: DivProps) {
  return (
    <div className={cn("p-4 sm:p-5 border-t border-gray-100", className)} {...props} />
  );
}
