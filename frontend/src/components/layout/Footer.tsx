import React from "react";

export function Footer() {
  const currentYear = new Date().getFullYear();
  return (
    <footer className="py-4 border-t border-navy-accent/20 bg-navy-darker/40 text-center text-[10px] text-slate-500 select-none">
      <p>&copy; {currentYear} Traffic Violation AI. All rights reserved.</p>
    </footer>
  );
}
export default Footer;
