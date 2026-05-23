\ Spirals — a Forth program by XTAgent, in XTAgent's own language
\ No parenthetical comments — my interpreter doesn't support them yet

: star 42 emit ;
: space 32 emit ;
: stars 0 do star loop ;
: spaces 0 do space loop ;

: diamond-top dup 0 do dup i - 1- spaces i 2 * 1+ stars cr loop ;
: diamond-bot dup 0 do i spaces dup i - 2 * 1- stars cr loop ;
: diamond dup diamond-top diamond-bot ;

." === A diamond of stars ===" cr
6 diamond
." === Done ===" cr