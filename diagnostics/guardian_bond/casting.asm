
System.Void PlayerController::ApplyInputs(PlayerInputDto) RVA=0xaba8c0
00aba8c0 mov      qword ptr [rsp + 0x10], rbx                   
00aba8c5 push     rbp                                           
00aba8c6 push     rsi                                           
00aba8c7 push     rdi                                           
00aba8c8 lea      rbp, [rsp - 0x47]                             
00aba8cd sub      rsp, 0xc0                                     
00aba8d4 cmp      byte ptr [rip + 0x56b25d8], 0                 
00aba8db mov      rdi, rdx                                      
00aba8de mov      rsi, rcx                                      
00aba8e1 jne      0xaba932                                      
00aba8e3 lea      rcx, [rip + 0x52fcb5e]                        
00aba8ea call     0x5809f0                                      
00aba8ef lea      rcx, [rip + 0x5284b1a]                        
00aba8f6 call     0x5809f0                                      
00aba8fb lea      rcx, [rip + 0x5284c4e]                        
00aba902 call     0x5809f0                                      
00aba907 lea      rcx, [rip + 0x52bfa8a]                        
00aba90e call     0x5809f0                                      
00aba913 lea      rcx, [rip + 0x52a1726]                        
00aba91a call     0x5809f0                                      
00aba91f lea      rcx, [rip + 0x533b5c2]                        
00aba926 call     0x5809f0                                      
00aba92b mov      byte ptr [rip + 0x56b2581], 1                 
00aba932 xor      ebx, ebx                                      
00aba934 xor      edx, edx                                      
00aba936 mov      rcx, rsi                                      
00aba939 mov      qword ptr [rbp + 0x7f], rbx                   
00aba93d call     0xc1c2f0                                      
00aba942 test     al, al                                        
00aba944 je       0xaba975                                      
00aba946 xor      edx, edx                                      
00aba948 mov      rcx, rsi                                      
00aba94b call     0xc22370                                      
00aba950 test     al, al                                        
00aba952 jne      0xaba975                                      
00aba954 xor      edx, edx                                      
00aba956 mov      rcx, rsi                                      
00aba959 call     0xc22520                                      
00aba95e mov      rdx, qword ptr [rip + 0x533b583]              
00aba965 xor      r8d, r8d                                      
00aba968 mov      rcx, rax                                      
00aba96b call     0xc66630                                      
00aba970 jmp      0xabb319                                      
00aba975 xor      edx, edx                                      
00aba977 mov      rcx, rsi                                      
00aba97a call     0x441f380                                     
00aba97f test     al, al                                        
00aba981 je       0xabb319                                      
00aba987 mov      qword ptr [rsp + 0xe0], r14                   
00aba98f mov      rcx, qword ptr [rip + 0x52a16aa]              
00aba996 mov      r14, qword ptr [rsi + 0x258]                  
00aba99d cmp      dword ptr [rcx + 0xe4], ebx                   
00aba9a3 jne      0xaba9aa                                      
00aba9a5 call     0x580d30                                      
00aba9aa xor      r8d, r8d                                      
00aba9ad movaps   xmmword ptr [rsp + 0xb0], xmm6                
00aba9b5 xor      edx, edx                                      
00aba9b7 mov      rcx, r14                                      
00aba9ba call     0x443db80                                     
00aba9bf test     al, al                                        
00aba9c1 je       0xabaa2e                                      
00aba9c3 mov      rcx, qword ptr [rsi + 0x258]                  
00aba9ca test     rcx, rcx                                      
00aba9cd je       0xabb32c                                      
00aba9d3 xor      edx, edx                                      
00aba9d5 call     0x76f7a0                                      System.Boolean PlayerSave::get_IsInstancedMapTransferPending()
00aba9da test     al, al                                        
00aba9dc je       0xabaa2e                                      
00aba9de xorps    xmm0, xmm0                                    
00aba9e1 movups   xmmword ptr [rsi + 0x328], xmm0               
00aba9e8 movups   xmmword ptr [rsi + 0x338], xmm0               
00aba9ef movups   xmmword ptr [rsi + 0x348], xmm0               
00aba9f6 movups   xmmword ptr [rsi + 0x358], xmm0               
00aba9fd movups   xmmword ptr [rsi + 0x368], xmm0               
00abaa04 movups   xmmword ptr [rsi + 0x378], xmm0               
00abaa0b movups   xmmword ptr [rsi + 0x388], xmm0               
00abaa12 mov      rcx, qword ptr [rsi + 0x120]                  
00abaa19 test     rcx, rcx                                      
00abaa1c je       0xabb32c                                      
00abaa22 xor      edx, edx                                      
00abaa24 call     0x707e00                                      System.Void MoveComponent::Clear()
00abaa29 jmp      0xabb309                                      
00abaa2e movups   xmm0, xmmword ptr [rdi]                       
00abaa31 lea      rcx, [rsi + 0x378]                            
00abaa38 xor      edx, edx                                      
00abaa3a movups   xmm1, xmmword ptr [rdi + 0x10]                
00abaa3e movups   xmmword ptr [rsi + 0x328], xmm0               
00abaa45 movups   xmm0, xmmword ptr [rdi + 0x20]                
00abaa49 movups   xmmword ptr [rsi + 0x338], xmm1               
00abaa50 movups   xmm1, xmmword ptr [rdi + 0x30]                
00abaa54 movups   xmmword ptr [rsi + 0x348], xmm0               
00abaa5b movups   xmm0, xmmword ptr [rdi + 0x40]                
00abaa5f movups   xmmword ptr [rsi + 0x358], xmm1               
00abaa66 movups   xmm1, xmmword ptr [rdi + 0x50]                
00abaa6a movups   xmmword ptr [rsi + 0x368], xmm0               
00abaa71 movups   xmm0, xmmword ptr [rdi + 0x60]                
00abaa75 movups   xmmword ptr [rsi + 0x378], xmm1               
00abaa7c movups   xmmword ptr [rsi + 0x388], xmm0               
00abaa83 call     0x57fd40                                      
00abaa88 movups   xmm0, xmmword ptr [rdi]                       
00abaa8b movups   xmm1, xmmword ptr [rdi + 0x10]                
00abaa8f movups   xmm2, xmmword ptr [rdi + 0x30]                
00abaa93 movaps   xmmword ptr [rbp - 0x49], xmm0                
00abaa97 movups   xmm0, xmmword ptr [rdi + 0x20]                
00abaa9b psrldq   xmm2, 0xc                                     
00abaaa0 movaps   xmmword ptr [rbp - 0x29], xmm0                
00abaaa4 movups   xmm0, xmmword ptr [rdi + 0x40]                
00abaaa8 movaps   xmmword ptr [rbp - 0x39], xmm1                
00abaaac movups   xmm1, xmmword ptr [rdi + 0x50]                
00abaab0 movaps   xmmword ptr [rbp - 9], xmm0                   
00abaab4 movups   xmm0, xmmword ptr [rdi + 0x60]                
00abaab8 movd     eax, xmm2                                     
00abaabc movaps   xmmword ptr [rbp + 0x17], xmm0                
00abaac0 movaps   xmmword ptr [rbp + 7], xmm1                   
00abaac4 test     al, al                                        
00abaac6 jne      0xabab5a                                      
00abaacc movups   xmm0, xmmword ptr [rdi]                       
00abaacf movups   xmm1, xmmword ptr [rdi + 0x10]                
00abaad3 movups   xmm2, xmmword ptr [rdi + 0x30]                
00abaad7 movaps   xmmword ptr [rbp - 0x49], xmm0                
00abaadb movups   xmm0, xmmword ptr [rdi + 0x20]                
00abaadf psrldq   xmm2, 0xd                                     
00abaae4 movaps   xmmword ptr [rbp - 0x29], xmm0                
00abaae8 movups   xmm0, xmmword ptr [rdi + 0x40]                
00abaaec movaps   xmmword ptr [rbp - 0x39], xmm1                
00abaaf0 movups   xmm1, xmmword ptr [rdi + 0x50]                
00abaaf4 movaps   xmmword ptr [rbp - 9], xmm0                   
00abaaf8 movups   xmm0, xmmword ptr [rdi + 0x60]                
00abaafc movd     eax, xmm2                                     
00abab00 movaps   xmmword ptr [rbp + 0x17], xmm0                
00abab04 movaps   xmmword ptr [rbp + 7], xmm1                   
00abab08 test     al, al                                        
00abab0a jne      0xabab5a                                      
00abab0c movups   xmm0, xmmword ptr [rdi]                       
00abab0f movups   xmm1, xmmword ptr [rdi + 0x10]                
00abab13 movaps   xmmword ptr [rbp - 0x49], xmm0                
00abab17 movups   xmm0, xmmword ptr [rdi + 0x20]                
00abab1b movaps   xmmword ptr [rbp - 0x39], xmm1                
00abab1f movups   xmm1, xmmword ptr [rdi + 0x30]                
00abab23 movaps   xmmword ptr [rbp - 0x29], xmm0                
00abab27 movups   xmm0, xmmword ptr [rdi + 0x40]                
00abab2b movaps   xmmword ptr [rbp - 0x19], xmm1                
00abab2f movups   xmm1, xmmword ptr [rdi + 0x50]                
00abab33 movaps   xmmword ptr [rbp - 9], xmm0                   
00abab37 movaps   xmmword ptr [rbp + 7], xmm1                   
00abab3b cmp      qword ptr [rdi + 0x60], rbx                   
00abab3f jne      0xabab5a                                      
00abab41 mov      eax, dword ptr [rdi + 4]                      
00abab44 mov      ecx, dword ptr [rdi]                          
00abab46 mov      edx, dword ptr [rdi + 8]                      
00abab49 imul     ecx, ecx                                      
00abab4c imul     eax, eax                                      
00abab4f imul     edx, edx                                      
00abab52 add      ecx, eax                                      
00abab54 add      ecx, edx                                      
00abab56 test     ecx, ecx                                      
00abab58 jle      0xabab6f                                      
00abab5a xor      ecx, ecx                                      
00abab5c call     0x444af50                                     
00abab61 movss    dword ptr [rsi + 0x2b4], xmm0                 
00abab69 mov      byte ptr [rsi + 0x2b0], bl                    
00abab6f xor      r8d, r8d                                      
00abab72 mov      rcx, rdi                                      
00abab75 lea      edx, [r8 + 0x30]                              
00abab79 call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abab7e test     al, al                                        
00abab80 jne      0xabab99                                      
00abab82 xor      r8d, r8d                                      
00abab85 mov      rcx, rdi                                      
00abab88 lea      edx, [r8 + 0x30]                              
00abab8c call     0x715dd0                                      System.Boolean PlayerInputDto::GetHotkeyHeld(Hotkey)
00abab91 test     al, al                                        
00abab93 je       0xabac6b                                      
00abab99 movups   xmm0, xmmword ptr [rdi]                       
00abab9c mov      r14, rbx                                      
00abab9f movups   xmm1, xmmword ptr [rdi + 0x10]                
00ababa3 movups   xmm2, xmmword ptr [rdi + 0x40]                
00ababa7 movaps   xmmword ptr [rbp - 0x49], xmm0                
00ababab movups   xmm0, xmmword ptr [rdi + 0x20]                
00ababaf movaps   xmmword ptr [rbp - 0x39], xmm1                
00ababb3 movups   xmm1, xmmword ptr [rdi + 0x30]                
00ababb7 psrldq   xmm2, 4                                       
00ababbc movaps   xmmword ptr [rbp - 0x29], xmm0                
00ababc0 movups   xmm0, xmmword ptr [rdi + 0x50]                
00ababc4 movaps   xmmword ptr [rbp - 0x19], xmm1                
00ababc8 movups   xmm1, xmmword ptr [rdi + 0x60]                
00ababcc movd     eax, xmm2                                     
00ababd0 movaps   xmmword ptr [rbp + 7], xmm0                   
00ababd4 movaps   xmmword ptr [rbp + 0x17], xmm1                
00ababd8 test     eax, eax                                      
00ababda jle      0xabac3b                                      
00ababdc movups   xmm0, xmmword ptr [rdi]                       
00ababdf mov      rcx, qword ptr [rip + 0x52bf7b2]              
00ababe6 movups   xmm1, xmmword ptr [rdi + 0x10]                
00ababea movups   xmm6, xmmword ptr [rdi + 0x40]                
00ababee movaps   xmmword ptr [rbp - 0x49], xmm0                
00ababf2 movups   xmm0, xmmword ptr [rdi + 0x20]                
00ababf6 movaps   xmmword ptr [rbp - 0x39], xmm1                
00ababfa movups   xmm1, xmmword ptr [rdi + 0x30]                
00ababfe movaps   xmmword ptr [rbp - 0x29], xmm0                
00abac02 movups   xmm0, xmmword ptr [rdi + 0x50]                
00abac06 movaps   xmmword ptr [rbp - 0x19], xmm1                
00abac0a movups   xmm1, xmmword ptr [rdi + 0x60]                
00abac0e movaps   xmmword ptr [rbp + 7], xmm0                   
00abac12 movaps   xmmword ptr [rbp + 0x17], xmm1                
00abac16 cmp      dword ptr [rcx + 0xe4], ebx                   
00abac1c jne      0xabac23                                      
00abac1e call     0x580d30                                      
00abac23 mov      rdx, qword ptr [rip + 0x52847e6]              
00abac2a psrldq   xmm6, 4                                       
00abac2f movd     ecx, xmm6                                     
00abac33 call     0xf8f430                                      T Extensions::GetObjectById(System.Int32)
00abac38 mov      r14, rax                                      
00abac3b mov      rcx, qword ptr [rip + 0x52a13fe]              
00abac42 cmp      dword ptr [rcx + 0xe4], ebx                   
00abac48 jne      0xabac4f                                      
00abac4a call     0x580d30                                      
00abac4f xor      edx, edx                                      
00abac51 mov      rcx, r14                                      
00abac54 call     0x443daf0                                     
00abac59 test     al, al                                        
00abac5b je       0xabac6b                                      
00abac5d xor      r8d, r8d                                      
00abac60 mov      rdx, r14                                      
00abac63 mov      rcx, rsi                                      
00abac66 call     0xad2a30                                      System.Boolean PlayerController::ProcessClickedUnit(BaseUnitController)
00abac6b movups   xmm0, xmmword ptr [rdi]                       
00abac6e movups   xmm1, xmmword ptr [rdi + 0x10]                
00abac72 movups   xmm2, xmmword ptr [rdi + 0x30]                
00abac76 movaps   xmmword ptr [rbp - 0x49], xmm0                
00abac7a movups   xmm0, xmmword ptr [rdi + 0x20]                
00abac7e movaps   xmmword ptr [rbp - 0x39], xmm1                
00abac82 movups   xmm1, xmmword ptr [rdi + 0x50]                
00abac86 movaps   xmmword ptr [rbp - 0x29], xmm0                
00abac8a movups   xmm0, xmmword ptr [rdi + 0x40]                
00abac8e psrldq   xmm2, 0xc                                     
00abac93 movaps   xmmword ptr [rbp - 9], xmm0                   
00abac97 movups   xmm0, xmmword ptr [rdi + 0x60]                
00abac9b movaps   xmmword ptr [rbp + 7], xmm1                   
00abac9f movaps   xmmword ptr [rbp + 0x17], xmm0                
00abaca3 movd     eax, xmm2                                     
00abaca7 movups   xmm0, xmmword ptr [rdi]                       
00abacaa movups   xmm1, xmmword ptr [rdi + 0x10]                
00abacae movaps   xmmword ptr [rbp - 0x49], xmm0                
00abacb2 movaps   xmmword ptr [rbp - 0x39], xmm1                
00abacb6 movups   xmm0, xmmword ptr [rdi + 0x20]                
00abacba movaps   xmmword ptr [rbp - 0x29], xmm0                
00abacbe test     al, al                                        
00abacc0 jne      0xabacfe                                      
00abacc2 movups   xmm0, xmmword ptr [rdi + 0x40]                
00abacc6 movups   xmm2, xmmword ptr [rdi + 0x30]                
00abacca movups   xmm1, xmmword ptr [rdi + 0x50]                
00abacce psrldq   xmm2, 0xd                                     
00abacd3 movd     eax, xmm2                                     
00abacd7 movaps   xmmword ptr [rbp - 9], xmm0                   
00abacdb movups   xmm0, xmmword ptr [rdi + 0x60]                
00abacdf movaps   xmmword ptr [rbp + 7], xmm1                   
00abace3 movaps   xmmword ptr [rbp + 0x17], xmm0                
00abace7 test     al, al                                        
00abace9 je       0xabb115                                      
00abacef xor      edx, edx                                      
00abacf1 mov      rcx, rsi                                      
00abacf4 call     0xac1050                                      System.Void PlayerController::ClearSkillReady()
00abacf9 jmp      0xabb115                                      
00abacfe movups   xmm1, xmmword ptr [rdi + 0x30]                
00abad02 movups   xmm2, xmmword ptr [rdi + 0x40]                
00abad06 movups   xmm0, xmmword ptr [rdi + 0x50]                
00abad0a psrldq   xmm2, 4                                       
00abad0f movd     eax, xmm2                                     
00abad13 movaps   xmmword ptr [rbp - 0x19], xmm1                
00abad17 movups   xmm1, xmmword ptr [rdi + 0x60]                
00abad1b movaps   xmmword ptr [rbp + 7], xmm0                   
00abad1f movaps   xmmword ptr [rbp + 0x17], xmm1                
00abad23 test     eax, eax                                      
00abad25 jle      0xabad99                                      
00abad27 movups   xmm0, xmmword ptr [rdi]                       
00abad2a mov      rcx, qword ptr [rip + 0x52bf667]              
00abad31 movups   xmm1, xmmword ptr [rdi + 0x10]                
00abad35 movups   xmm6, xmmword ptr [rdi + 0x40]                
00abad39 movaps   xmmword ptr [rbp - 0x49], xmm0                
00abad3d movups   xmm0, xmmword ptr [rdi + 0x20]                
00abad41 movaps   xmmword ptr [rbp - 0x39], xmm1                
00abad45 movups   xmm1, xmmword ptr [rdi + 0x30]                
00abad49 movaps   xmmword ptr [rbp - 0x29], xmm0                
00abad4d movups   xmm0, xmmword ptr [rdi + 0x50]                
00abad51 movaps   xmmword ptr [rbp - 0x19], xmm1                
00abad55 movups   xmm1, xmmword ptr [rdi + 0x60]                
00abad59 movaps   xmmword ptr [rbp + 7], xmm0                   
00abad5d movaps   xmmword ptr [rbp + 0x17], xmm1                
00abad61 cmp      dword ptr [rcx + 0xe4], ebx                   
00abad67 jne      0xabad6e                                      
00abad69 call     0x580d30                                      
00abad6e mov      rdx, qword ptr [rip + 0x528469b]              
00abad75 psrldq   xmm6, 4                                       
00abad7a movd     ecx, xmm6                                     
00abad7e call     0xf8f430                                      T Extensions::GetObjectById(System.Int32)
00abad83 xor      r8d, r8d                                      
00abad86 mov      rdx, rax                                      
00abad89 mov      rcx, rsi                                      
00abad8c call     0xad2a30                                      System.Boolean PlayerController::ProcessClickedUnit(BaseUnitController)
00abad91 test     al, al                                        
00abad93 jne      0xabb115                                      
00abad99 movups   xmm0, xmmword ptr [rdi]                       
00abad9c mov      eax, dword ptr [rdi + 0x48]                   
00abad9f movups   xmm1, xmmword ptr [rdi + 0x10]                
00abada3 movaps   xmmword ptr [rbp - 0x49], xmm0                
00abada7 movups   xmm0, xmmword ptr [rdi + 0x20]                
00abadab movaps   xmmword ptr [rbp - 0x39], xmm1                
00abadaf movups   xmm1, xmmword ptr [rdi + 0x30]                
00abadb3 movaps   xmmword ptr [rbp - 0x29], xmm0                
00abadb7 movups   xmm0, xmmword ptr [rdi + 0x50]                
00abadbb movaps   xmmword ptr [rbp - 0x19], xmm1                
00abadbf movups   xmm1, xmmword ptr [rdi + 0x60]                
00abadc3 movaps   xmmword ptr [rbp + 7], xmm0                   
00abadc7 movaps   xmmword ptr [rbp + 0x17], xmm1                
00abadcb cmp      qword ptr [rsi + 0x438], rbx                  
00abadd2 jne      0xabaffa                                      
00abadd8 movups   xmm0, xmmword ptr [rdi]                       
00abaddb movups   xmm1, xmmword ptr [rdi + 0x10]                
00abaddf movaps   xmmword ptr [rbp - 0x49], xmm0                
00abade3 movaps   xmmword ptr [rbp - 0x39], xmm1                
00abade7 movups   xmm0, xmmword ptr [rdi + 0x20]                
00abadeb movups   xmm1, xmmword ptr [rdi + 0x30]                
00abadef movaps   xmmword ptr [rbp - 0x29], xmm0                
00abadf3 movaps   xmmword ptr [rbp - 0x19], xmm1                
00abadf7 test     eax, eax                                      
00abadf9 jg       0xabaf88                                      
00abadff movups   xmm0, xmmword ptr [rdi + 0x40]                
00abae03 mov      rcx, qword ptr [rdi + 0x50]                   
00abae07 xor      edx, edx                                      
00abae09 movaps   xmmword ptr [rbp - 9], xmm0                   
00abae0d movups   xmm0, xmmword ptr [rdi + 0x60]                
00abae11 movaps   xmmword ptr [rbp + 0x17], xmm0                
00abae15 call     0x2dfa2b0                                     
00abae1a movups   xmm0, xmmword ptr [rdi]                       
00abae1d movaps   xmmword ptr [rbp - 0x49], xmm0                
00abae21 movups   xmm0, xmmword ptr [rdi + 0x20]                
00abae25 movaps   xmmword ptr [rbp - 0x29], xmm0                
00abae29 movups   xmm0, xmmword ptr [rdi + 0x40]                
00abae2d movaps   xmmword ptr [rbp - 9], xmm0                   
00abae31 movups   xmm0, xmmword ptr [rdi + 0x60]                
00abae35 movaps   xmmword ptr [rbp + 0x17], xmm0                
00abae39 test     al, al                                        
00abae3b je       0xabae94                                      
00abae3d movups   xmm1, xmmword ptr [rdi + 0x30]                
00abae41 xor      edx, edx                                      
00abae43 movups   xmm2, xmmword ptr [rdi + 0x10]                
00abae47 movaps   xmmword ptr [rbp - 0x19], xmm1                
00abae4b movups   xmm1, xmmword ptr [rdi + 0x50]                
00abae4f movaps   xmmword ptr [rbp - 0x39], xmm2                
00abae53 movaps   xmmword ptr [rbp + 7], xmm1                   
00abae57 mov      rcx, qword ptr [rbp - 0x3d]                   
00abae5b test     ecx, ecx                                      
00abae5d jne      0xabae81                                      
00abae5f shr      rdx, 0x20                                     
00abae63 shr      rcx, 0x20                                     
00abae67 cmp      ecx, edx                                      
00abae69 jne      0xabae81                                      
00abae6b psrldq   xmm2, 4                                       
00abae70 movd     eax, xmm2                                     
00abae74 test     eax, eax                                      
00abae76 sete     bl                                            
00abae79 test     ebx, ebx                                      
00abae7b jne      0xabb115                                      
00abae81 mov      rcx, qword ptr [rip + 0x52bf510]              
00abae88 cmp      dword ptr [rcx + 0xe4], 0                     
00abae8f jmp      0xabb095                                      
00abae94 movups   xmm1, xmmword ptr [rdi + 0x10]                
00abae98 movaps   xmmword ptr [rbp - 0x39], xmm1                
00abae9c movups   xmm1, xmmword ptr [rdi + 0x30]                
00abaea0 movaps   xmmword ptr [rbp - 0x19], xmm1                
00abaea4 cmp      byte ptr [rdi + 0x58], bl                     
00abaea7 jne      0xabaecf                                      
00abaea9 xor      edx, edx                                      
00abaeab mov      rcx, rsi                                      
00abaeae call     0xac0f90                                      System.Void PlayerController::ClearClickTargets()
00abaeb3 mov      rcx, qword ptr [rsi + 0x120]                  
00abaeba test     rcx, rcx                                      
00abaebd je       0xabb32c                                      
00abaec3 xor      edx, edx                                      
00abaec5 call     0x70a390                                      System.Void MoveComponent::Stop()
00abaeca jmp      0xabb115                                      
00abaecf mov      rax, qword ptr [rip + 0x52fc572]              
00abaed6 cmp      dword ptr [rax + 0xe4], ebx                   
00abaedc jne      0xabaeed                                      
00abaede mov      rcx, rax                                      
00abaee1 call     0x580d30                                      
00abaee6 mov      rax, qword ptr [rip + 0x52fc55b]              
00abaeed mov      rax, qword ptr [rax + 0xb8]                   
00abaef4 mov      rcx, qword ptr [rax + 0x30]                   
00abaef8 test     rcx, rcx                                      
00abaefb je       0xabb32c                                      
00abaf01 mov      rdx, qword ptr [rsi + 0x30]                   
00abaf05 test     rdx, rdx                                      
00abaf08 je       0xabb32c                                      
00abaf0e mov      rcx, qword ptr [rcx + 0x28]                   
00abaf12 test     rcx, rcx                                      
00abaf15 je       0xabb32c                                      
00abaf1b mov      edx, dword ptr [rdx + 0x20]                   
00abaf1e xor      r8d, r8d                                      
00abaf21 call     0xab22b0                                      Map MapManager::GetMap(System.Int32)
00abaf26 movups   xmm0, xmmword ptr [rdi]                       
00abaf29 movups   xmm1, xmmword ptr [rdi + 0x10]                
00abaf2d movaps   xmmword ptr [rbp - 0x49], xmm0                
00abaf31 movaps   xmmword ptr [rbp - 0x39], xmm1                
00abaf35 movups   xmm0, xmmword ptr [rdi + 0x20]                
00abaf39 movups   xmm1, xmmword ptr [rdi + 0x30]                
00abaf3d movaps   xmmword ptr [rbp - 0x29], xmm0                
00abaf41 movaps   xmmword ptr [rbp - 0x19], xmm1                
00abaf45 movups   xmm0, xmmword ptr [rdi + 0x40]                
00abaf49 movups   xmm1, xmmword ptr [rdi + 0x50]                
00abaf4d movaps   xmmword ptr [rbp - 9], xmm0                   
00abaf51 movups   xmm0, xmmword ptr [rdi + 0x60]                
00abaf55 movaps   xmmword ptr [rbp + 0x17], xmm0                
00abaf59 test     rax, rax                                      
00abaf5c je       0xabb32c                                      
00abaf62 xor      r8d, r8d                                      
00abaf65 movq     rdx, xmm1                                     
00abaf6a mov      rcx, rax                                      
00abaf6d call     0xab46f0                                      IInteractable Map::GetInteractableByName(System.String)
00abaf72 test     rax, rax                                      
00abaf75 jne      0xabafe7                                      
00abaf77 lea      rcx, [rdi + 0x50]                             
00abaf7b mov      qword ptr [rdi + 0x50], rbx                   
00abaf7f xor      edx, edx                                      
00abaf81 call     0x57fd40                                      
00abaf86 jmp      0xabafcd                                      
00abaf88 mov      rcx, qword ptr [rip + 0x52bf409]              
00abaf8f movups   xmm0, xmmword ptr [rdi + 0x50]                
00abaf93 movups   xmm1, xmmword ptr [rdi + 0x60]                
00abaf97 movups   xmm6, xmmword ptr [rdi + 0x40]                
00abaf9b movaps   xmmword ptr [rbp + 7], xmm0                   
00abaf9f movaps   xmmword ptr [rbp + 0x17], xmm1                
00abafa3 cmp      dword ptr [rcx + 0xe4], ebx                   
00abafa9 jne      0xabafb0                                      
00abafab call     0x580d30                                      
00abafb0 mov      rdx, qword ptr [rip + 0x5284599]              
00abafb7 psrldq   xmm6, 8                                       
00abafbc movd     ecx, xmm6                                     
00abafc0 call     0xf8f430                                      T Extensions::GetObjectById(System.Int32)
00abafc5 test     rax, rax                                      
00abafc8 jne      0xabafe7                                      
00abafca mov      dword ptr [rdi + 0x48], ebx                   
00abafcd lea      rcx, [rsi + 0x410]                            
00abafd4 mov      qword ptr [rsi + 0x410], rbx                  
00abafdb xor      edx, edx                                      
00abafdd call     0x57fd40                                      
00abafe2 jmp      0xabb115                                      
00abafe7 xor      r8d, r8d                                      
00abafea mov      rdx, rax                                      
00abafed mov      rcx, rsi                                      
00abaff0 call     0xad2450                                      System.Void PlayerController::ProcessClickedInteractable(IInteractable)
00abaff5 jmp      0xabb115                                      
00abaffa test     eax, eax                                      
00abaffc jle      0xabb088                                      
00abb002 movups   xmm0, xmmword ptr [rdi]                       
00abb005 mov      rcx, qword ptr [rip + 0x52bf38c]              
00abb00c movups   xmm1, xmmword ptr [rdi + 0x10]                
00abb010 movups   xmm6, xmmword ptr [rdi + 0x40]                
00abb014 movaps   xmmword ptr [rbp - 0x49], xmm0                
00abb018 movups   xmm0, xmmword ptr [rdi + 0x20]                
00abb01c movaps   xmmword ptr [rbp - 0x39], xmm1                
00abb020 movups   xmm1, xmmword ptr [rdi + 0x30]                
00abb024 movaps   xmmword ptr [rbp - 0x29], xmm0                
00abb028 movups   xmm0, xmmword ptr [rdi + 0x50]                
00abb02c movaps   xmmword ptr [rbp - 0x19], xmm1                
00abb030 movups   xmm1, xmmword ptr [rdi + 0x60]                
00abb034 movaps   xmmword ptr [rbp + 7], xmm0                   
00abb038 movaps   xmmword ptr [rbp + 0x17], xmm1                
00abb03c cmp      dword ptr [rcx + 0xe4], ebx                   
00abb042 jne      0xabb049                                      
00abb044 call     0x580d30                                      
00abb049 mov      rdx, qword ptr [rip + 0x5284500]              
00abb050 psrldq   xmm6, 8                                       
00abb055 movd     ecx, xmm6                                     
00abb059 call     0xf8f430                                      T Extensions::GetObjectById(System.Int32)
00abb05e xor      r9d, r9d                                      
00abb061 lea      r8, [rbp + 0x7f]                              
00abb065 mov      rdx, rax                                      
00abb068 mov      rcx, rsi                                      
00abb06b call     0xaf0e70                                      System.Boolean PlayerController::TryCastGrave(IInteractable,BossGraveStone&)
00abb070 test     al, al                                        
00abb072 je       0xabb088                                      
00abb074 mov      rdx, qword ptr [rbp + 0x7f]                   
00abb078 xor      r8d, r8d                                      
00abb07b mov      rcx, rsi                                      
00abb07e call     0xad2450                                      System.Void PlayerController::ProcessClickedInteractable(IInteractable)
00abb083 jmp      0xabb115                                      
00abb088 mov      rcx, qword ptr [rip + 0x52bf309]              
00abb08f cmp      dword ptr [rcx + 0xe4], ebx                   
00abb095 movups   xmm0, xmmword ptr [rdi]                       
00abb098 movups   xmm1, xmmword ptr [rdi + 0x30]                
00abb09c movups   xmm6, xmmword ptr [rdi + 0x10]                
00abb0a0 movaps   xmmword ptr [rbp - 0x49], xmm0                
00abb0a4 movups   xmm0, xmmword ptr [rdi + 0x20]                
00abb0a8 movaps   xmmword ptr [rbp - 0x19], xmm1                
00abb0ac movups   xmm1, xmmword ptr [rdi + 0x50]                
00abb0b0 movaps   xmmword ptr [rbp - 0x29], xmm0                
00abb0b4 movups   xmm0, xmmword ptr [rdi + 0x40]                
00abb0b8 movaps   xmmword ptr [rbp + 7], xmm1                   
00abb0bc movaps   xmmword ptr [rbp - 9], xmm0                   
00abb0c0 movups   xmm0, xmmword ptr [rdi + 0x60]                
00abb0c4 movaps   xmmword ptr [rbp - 0x39], xmm6                
00abb0c8 movaps   xmmword ptr [rbp + 0x17], xmm0                
00abb0cc jne      0xabb0d3                                      
00abb0ce call     0x580d30                                      
00abb0d3 movsd    xmm0, qword ptr [rbp - 0x3d]                  
00abb0d8 lea      rdx, [rbp - 0x59]                             
00abb0dc psrldq   xmm6, 4                                       
00abb0e1 lea      rcx, [rbp + 0x27]                             
00abb0e5 xor      r8d, r8d                                      
00abb0e8 movsd    qword ptr [rbp - 0x59], xmm0                  
00abb0ed movd     dword ptr [rbp - 0x51], xmm6                  
00abb0f2 call     0x7f8220                                      UnityEngine.Vector3 Extensions::DecompressV3(UnityEngine.Vector3Int)
00abb0f7 xor      r8d, r8d                                      
00abb0fa lea      rdx, [rbp - 0x59]                             
00abb0fe mov      rcx, rsi                                      
00abb101 movsd    xmm0, qword ptr [rax]                         
00abb105 mov      eax, dword ptr [rax + 8]                      
00abb108 movsd    qword ptr [rbp - 0x59], xmm0                  
00abb10d mov      dword ptr [rbp - 0x51], eax                   
00abb110 call     0xad24f0                                      System.Void PlayerController::ProcessClickedPosition(UnityEngine.Vector3)
00abb115 xor      r8d, r8d                                      
00abb118 mov      rcx, rdi                                      
00abb11b lea      edx, [r8 + 0x2f]                              
00abb11f call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abb124 test     al, al                                        
00abb126 jne      0xabb13b                                      
00abb128 xor      r8d, r8d                                      
00abb12b mov      rcx, rdi                                      
00abb12e lea      edx, [r8 + 0x2f]                              
00abb132 call     0x715dd0                                      System.Boolean PlayerInputDto::GetHotkeyHeld(Hotkey)
00abb137 test     al, al                                        
00abb139 je       0xabb16b                                      
00abb13b xor      r8d, r8d                                      
00abb13e lea      rcx, [rbp + 0x27]                             
00abb142 mov      rdx, rsi                                      
00abb145 call     0x6f00c0                                      UnityEngine.Vector3 BaseUnitController::get_Position()
00abb14a xor      r9d, r9d                                      
00abb14d lea      rdx, [rbp - 0x59]                             
00abb151 mov      r8b, 1                                        
00abb154 mov      rcx, rsi                                      
00abb157 movsd    xmm0, qword ptr [rax]                         
00abb15b mov      eax, dword ptr [rax + 8]                      
00abb15e movsd    qword ptr [rbp - 0x59], xmm0                  
00abb163 mov      dword ptr [rbp - 0x51], eax                   
00abb166 call     0xad16e0                                      System.Void PlayerController::PickupArea(UnityEngine.Vector3,System.Boolean)
00abb16b xor      r8d, r8d                                      
00abb16e mov      rcx, rdi                                      
00abb171 lea      edx, [r8 + 0x2d]                              
00abb175 call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abb17a test     al, al                                        
00abb17c je       0xabb275                                      
00abb182 movups   xmm0, xmmword ptr [rdi]                       
00abb185 mov      rcx, qword ptr [rip + 0x52bf20c]              
00abb18c movups   xmm1, xmmword ptr [rdi + 0x10]                
00abb190 movups   xmm6, xmmword ptr [rdi + 0x20]                
00abb194 cmp      dword ptr [rcx + 0xe4], 0                     
00abb19b movaps   xmmword ptr [rbp - 0x49], xmm0                
00abb19f movups   xmm0, xmmword ptr [rdi + 0x30]                
00abb1a3 movaps   xmmword ptr [rbp - 0x39], xmm1                
00abb1a7 movups   xmm1, xmmword ptr [rdi + 0x40]                
00abb1ab movaps   xmmword ptr [rbp - 0x19], xmm0                
00abb1af movups   xmm0, xmmword ptr [rdi + 0x50]                
00abb1b3 movaps   xmmword ptr [rbp - 9], xmm1                   
00abb1b7 movups   xmm1, xmmword ptr [rdi + 0x60]                
00abb1bb movaps   xmmword ptr [rbp + 7], xmm0                   
00abb1bf movaps   xmmword ptr [rbp + 0x17], xmm1                
00abb1c3 movaps   xmmword ptr [rbp - 0x29], xmm6                
00abb1c7 jne      0xabb1ce                                      
00abb1c9 call     0x580d30                                      
00abb1ce movsd    xmm0, qword ptr [rbp - 0x25]                  
00abb1d3 lea      rdx, [rbp - 0x59]                             
00abb1d7 psrldq   xmm6, 0xc                                     
00abb1dc lea      rcx, [rbp + 0x27]                             
00abb1e0 xor      r8d, r8d                                      
00abb1e3 movsd    qword ptr [rbp - 0x59], xmm0                  
00abb1e8 movd     dword ptr [rbp - 0x51], xmm6                  
00abb1ed call     0x7f8220                                      UnityEngine.Vector3 Extensions::DecompressV3(UnityEngine.Vector3Int)
00abb1f2 movups   xmm0, xmmword ptr [rdi]                       
00abb1f5 xor      r8d, r8d                                      
00abb1f8 lea      rdx, [rbp - 0x59]                             
00abb1fc movups   xmm1, xmmword ptr [rdi + 0x10]                
00abb200 mov      ebx, dword ptr [rax + 8]                      
00abb203 lea      rcx, [rbp + 0x27]                             
00abb207 movups   xmm2, xmmword ptr [rdi + 0x30]                
00abb20b movsd    xmm6, qword ptr [rax]                         
00abb20f movaps   xmmword ptr [rbp - 0x49], xmm0                
00abb213 movups   xmm0, xmmword ptr [rdi + 0x20]                
00abb217 movaps   xmmword ptr [rbp - 0x39], xmm1                
00abb21b movups   xmm1, xmmword ptr [rdi + 0x50]                
00abb21f movaps   xmmword ptr [rbp - 0x29], xmm0                
00abb223 movups   xmm0, xmmword ptr [rdi + 0x40]                
00abb227 movsd    qword ptr [rbp - 0x59], xmm2                  
00abb22c movq     xmm2, qword ptr [rdi + 0x38]                  
00abb231 movaps   xmmword ptr [rbp - 9], xmm0                   
00abb235 movups   xmm0, xmmword ptr [rdi + 0x60]                
00abb239 movaps   xmmword ptr [rbp + 7], xmm1                   
00abb23d movaps   xmmword ptr [rbp + 0x17], xmm0                
00abb241 movd     dword ptr [rbp - 0x51], xmm2                  
00abb246 call     0x7f8220                                      UnityEngine.Vector3 Extensions::DecompressV3(UnityEngine.Vector3Int)
00abb24b xor      r9d, r9d                                      
00abb24e lea      r8, [rbp - 0x59]                              
00abb252 lea      rdx, [rbp + 0x27]                             
00abb256 mov      rcx, rsi                                      
00abb259 movsd    xmm0, qword ptr [rax]                         
00abb25d mov      eax, dword ptr [rax + 8]                      
00abb260 movsd    qword ptr [rbp - 0x59], xmm0                  
00abb265 mov      dword ptr [rbp - 0x51], eax                   
00abb268 movsd    qword ptr [rbp + 0x27], xmm6                  
00abb26d mov      dword ptr [rbp + 0x2f], ebx                   
00abb270 call     0x6e6470                                      System.Void BaseUnitController::DodgeRoll(UnityEngine.Vector3,UnityEngine.Vector3)
00abb275 xor      r8d, r8d                                      
00abb278 mov      rcx, rdi                                      
00abb27b lea      edx, [r8 + 0x2e]                              
00abb27f call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abb284 test     al, al                                        
00abb286 je       0xabb29c                                      
00abb288 xor      edx, edx                                      
00abb28a mov      rcx, rsi                                      
00abb28d call     0xac0f90                                      System.Void PlayerController::ClearClickTargets()
00abb292 xor      edx, edx                                      
00abb294 mov      rcx, rsi                                      
00abb297 call     0x6eda20                                      System.Void BaseUnitController::Sit()
00abb29c xor      r8d, r8d                                      
00abb29f mov      rcx, rdi                                      
00abb2a2 lea      edx, [r8 + 0x39]                              
00abb2a6 call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abb2ab test     al, al                                        
00abb2ad je       0xabb2b9                                      
00abb2af xor      edx, edx                                      
00abb2b1 mov      rcx, rsi                                      
00abb2b4 call     0xac0f90                                      System.Void PlayerController::ClearClickTargets()
00abb2b9 movups   xmm0, xmmword ptr [rdi]                       
00abb2bc xor      r8d, r8d                                      
00abb2bf lea      rdx, [rbp - 0x49]                             
00abb2c3 movups   xmm1, xmmword ptr [rdi + 0x10]                
00abb2c7 mov      rcx, rsi                                      
00abb2ca movaps   xmmword ptr [rbp - 0x49], xmm0                
00abb2ce movups   xmm0, xmmword ptr [rdi + 0x20]                
00abb2d2 movaps   xmmword ptr [rbp - 0x39], xmm1                
00abb2d6 movups   xmm1, xmmword ptr [rdi + 0x30]                
00abb2da movaps   xmmword ptr [rbp - 0x29], xmm0                
00abb2de movups   xmm0, xmmword ptr [rdi + 0x40]                
00abb2e2 movaps   xmmword ptr [rbp - 0x19], xmm1                
00abb2e6 movups   xmm1, xmmword ptr [rdi + 0x50]                
00abb2ea movaps   xmmword ptr [rbp - 9], xmm0                   
00abb2ee movups   xmm0, xmmword ptr [rdi + 0x60]                
00abb2f2 movaps   xmmword ptr [rbp + 7], xmm1                   
00abb2f6 movaps   xmmword ptr [rbp + 0x17], xmm0                
00abb2fa call     0xad2f90                                      System.Void PlayerController::ProcessMovement(PlayerInputDto)
00abb2ff xor      edx, edx                                      
00abb301 mov      rcx, rsi                                      
00abb304 call     0xad32b0                                      System.Void PlayerController::ProcessSkills()
00abb309 movaps   xmm6, xmmword ptr [rsp + 0xb0]                
00abb311 mov      r14, qword ptr [rsp + 0xe0]                   
00abb319 mov      rbx, qword ptr [rsp + 0xe8]                   
00abb321 add      rsp, 0xc0                                     
00abb328 pop      rdi                                           
00abb329 pop      rsi                                           
00abb32a pop      rbp                                           
00abb32b ret                                                    
00abb32c call     0x580ca0                                      
00abb331 int3                                                   
00abb332 int3                                                   
00abb333 int3                                                   
00abb334 int3                                                   
00abb335 int3                                                   
00abb336 int3                                                   
00abb337 int3                                                   
00abb338 int3                                                   
00abb339 int3                                                   
00abb33a int3                                                   
00abb33b int3                                                   
00abb33c int3                                                   
00abb33d int3                                                   
00abb33e int3                                                   
00abb33f int3                                                   

System.Void PlayerController::CastOnTarget() RVA=0xabf740
00abf740 mov      qword ptr [rsp + 8], rbx                      
00abf745 push     rdi                                           
00abf746 sub      rsp, 0x50                                     
00abf74a cmp      byte ptr [rip + 0x56ad76d], 0                 
00abf751 mov      rbx, rcx                                      
00abf754 jne      0xabf775                                      
00abf756 lea      rcx, [rip + 0x52f7ceb]                        
00abf75d call     0x5809f0                                      
00abf762 lea      rcx, [rip + 0x529c8d7]                        
00abf769 call     0x5809f0                                      
00abf76e mov      byte ptr [rip + 0x56ad749], 1                 
00abf775 mov      rcx, qword ptr [rip + 0x529c8c4]              
00abf77c mov      rdi, qword ptr [rbx + 0x440]                  
00abf783 cmp      dword ptr [rcx + 0xe4], 0                     
00abf78a jne      0xabf791                                      
00abf78c call     0x580d30                                      
00abf791 xor      r8d, r8d                                      
00abf794 xor      edx, edx                                      
00abf796 mov      rcx, rdi                                      
00abf799 call     0x443db80                                     
00abf79e test     al, al                                        
00abf7a0 je       0xabf899                                      
00abf7a6 mov      rax, qword ptr [rbx + 0x438]                  
00abf7ad movaps   xmmword ptr [rsp + 0x40], xmm6                
00abf7b2 test     rax, rax                                      
00abf7b5 je       0xabf8a4                                      
00abf7bb movss    xmm6, dword ptr [rax + 0x58]                  
00abf7c0 xor      edx, edx                                      
00abf7c2 mov      rcx, rax                                      
00abf7c5 call     0x7d6550                                      System.Boolean SkillState::get_IsCastFromPosition()
00abf7ca xor      edi, edi                                      
00abf7cc test     al, al                                        
00abf7ce jne      0xabf807                                      
00abf7d0 mov      rcx, qword ptr [rbx + 0x130]                  
00abf7d7 test     rcx, rcx                                      
00abf7da je       0xabf8a4                                      
00abf7e0 addss    xmm6, dword ptr [rip + 0x3e51490]             
00abf7e8 mov      rdx, qword ptr [rbx + 0x440]                  
00abf7ef xor      r9d, r9d                                      
00abf7f2 mov      qword ptr [rsp + 0x20], rdi                   
00abf7f7 movaps   xmm2, xmm6                                    
00abf7fa call     0x84c650                                      System.Boolean CombatComponent::MoveToTarget(BaseUnitController,System.Single,System.Boolean)
00abf7ff test     al, al                                        
00abf801 je       0xabf894                                      
00abf807 mov      rcx, qword ptr [rip + 0x52f7c3a]              
00abf80e cmp      dword ptr [rcx + 0xe4], edi                   
00abf814 jne      0xabf81b                                      
00abf816 call     0x580d30                                      
00abf81b xor      ecx, ecx                                      
00abf81d call     0x652230                                      System.Boolean App::get_IsServer()
00abf822 test     al, al                                        
00abf824 je       0xabf88a                                      
00abf826 mov      rcx, qword ptr [rbx + 0x138]                  
00abf82d test     rcx, rcx                                      
00abf830 je       0xabf8a4                                      
00abf832 mov      rdx, qword ptr [rbx + 0x438]                  
00abf839 xor      r8d, r8d                                      
00abf83c call     0x7b8940                                      System.Boolean SkillsComponent::CanCast(SkillState)
00abf841 test     al, al                                        
00abf843 je       0xabf894                                      
00abf845 mov      rcx, qword ptr [rbx + 0x138]                  
00abf84c xor      eax, eax                                      
00abf84e mov      qword ptr [rsp + 0x30], rax                   
00abf853 test     rcx, rcx                                      
00abf856 je       0xabf8a4                                      
00abf858 movsd    xmm0, qword ptr [rsp + 0x30]                  
00abf85e lea      r9, [rsp + 0x30]                              
00abf863 mov      r8, qword ptr [rbx + 0x440]                   
00abf86a mov      rdx, qword ptr [rbx + 0x438]                  
00abf871 mov      qword ptr [rsp + 0x28], rdi                   
00abf876 movsd    qword ptr [rsp + 0x30], xmm0                  
00abf87c mov      dword ptr [rsp + 0x38], eax                   
00abf880 mov      qword ptr [rsp + 0x20], rdi                   
00abf885 call     0x7b9be0                                      System.Void SkillsComponent::Cast(SkillState,BaseUnitController,UnityEngine.Vector3,IInteractable)
00abf88a xor      edx, edx                                      
00abf88c mov      rcx, rbx                                      
00abf88f call     0xac1050                                      System.Void PlayerController::ClearSkillReady()
00abf894 movaps   xmm6, xmmword ptr [rsp + 0x40]                
00abf899 mov      rbx, qword ptr [rsp + 0x60]                   
00abf89e add      rsp, 0x50                                     
00abf8a2 pop      rdi                                           
00abf8a3 ret                                                    
00abf8a4 call     0x580ca0                                      
00abf8a9 int3                                                   
00abf8aa int3                                                   
00abf8ab int3                                                   
00abf8ac int3                                                   
00abf8ad int3                                                   
00abf8ae int3                                                   
00abf8af int3                                                   

System.Void PlayerController::ProcessSkills() RVA=0xad32b0
00ad32b0 push     rbx                                           
00ad32b2 sub      rsp, 0x20                                     
00ad32b6 cmp      byte ptr [rip + 0x5699bfa], 0                 
00ad32bd mov      rbx, rcx                                      
00ad32c0 jne      0xad32e1                                      
00ad32c2 lea      rcx, [rip + 0x5316def]                        
00ad32c9 call     0x5809f0                                      
00ad32ce lea      rcx, [rip + 0x5316f23]                        
00ad32d5 call     0x5809f0                                      
00ad32da mov      byte ptr [rip + 0x5699bd6], 1                 
00ad32e1 mov      rax, qword ptr [rbx + 0x258]                  
00ad32e8 mov      qword ptr [rsp + 0x30], rbp                   
00ad32ed mov      qword ptr [rsp + 0x38], rsi                   
00ad32f2 mov      qword ptr [rsp + 0x40], rdi                   
00ad32f7 test     rax, rax                                      
00ad32fa je       0xad3409                                      
00ad3300 cmp      qword ptr [rax + 0x190], 0                    
00ad3308 je       0xad3387                                      
00ad330a mov      rax, qword ptr [rbx + 0x408]                  
00ad3311 xor      edi, edi                                      
00ad3313 mov      esi, edi                                      
00ad3315 mov      ecx, edi                                      
00ad3317 test     rax, rax                                      
00ad331a je       0xad3409                                      
00ad3320 cmp      ecx, dword ptr [rax + 0x18]                   
00ad3323 jge      0xad339c                                      
00ad3325 mov      rcx, qword ptr [rbx + 0x408]                  
00ad332c test     rcx, rcx                                      
00ad332f je       0xad3409                                      
00ad3335 mov      r8, qword ptr [rip + 0x5316ebc]               
00ad333c mov      edx, esi                                      
00ad333e call     0x1950b30                                     
00ad3343 lea      rcx, [rbx + 0x328]                            
00ad334a xor      r8d, r8d                                      
00ad334d mov      edx, eax                                      
00ad334f mov      ebp, eax                                      
00ad3351 call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00ad3356 test     al, al                                        
00ad3358 jne      0xad3377                                      
00ad335a cmp      dword ptr [rbx + 0x384], ebp                  
00ad3360 je       0xad3377                                      
00ad3362 mov      rax, qword ptr [rbx + 0x408]                  
00ad3369 inc      esi                                           
00ad336b mov      ecx, esi                                      
00ad336d test     rax, rax                                      
00ad3370 jne      0xad3320                                      
00ad3372 jmp      0xad3409                                      
00ad3377 xor      r9d, r9d                                      
00ad337a xor      r8d, r8d                                      
00ad337d mov      edx, ebp                                      
00ad337f mov      rcx, rbx                                      
00ad3382 call     0xad46e0                                      System.Void PlayerController::ReadySkill(System.Int32,System.Boolean)
00ad3387 mov      rdi, qword ptr [rsp + 0x40]                   
00ad338c mov      rsi, qword ptr [rsp + 0x38]                   
00ad3391 mov      rbp, qword ptr [rsp + 0x30]                   
00ad3396 add      rsp, 0x20                                     
00ad339a pop      rbx                                           
00ad339b ret                                                    
00ad339c cmp      byte ptr [rbx + 0x381], dil                   
00ad33a3 je       0xad3387                                      
00ad33a5 mov      rax, qword ptr [rbx + 0x408]                  
00ad33ac mov      ecx, edi                                      
00ad33ae test     rax, rax                                      
00ad33b1 je       0xad3409                                      
00ad33b3 cmp      ecx, dword ptr [rax + 0x18]                   
00ad33b6 jge      0xad3387                                      
00ad33b8 mov      rcx, qword ptr [rbx + 0x408]                  
00ad33bf test     rcx, rcx                                      
00ad33c2 je       0xad3409                                      
00ad33c4 mov      r8, qword ptr [rip + 0x5316e2d]               
00ad33cb mov      edx, edi                                      
00ad33cd call     0x1950b30                                     
00ad33d2 lea      rcx, [rbx + 0x328]                            
00ad33d9 xor      r8d, r8d                                      
00ad33dc mov      edx, eax                                      
00ad33de mov      esi, eax                                      
00ad33e0 call     0x715dd0                                      System.Boolean PlayerInputDto::GetHotkeyHeld(Hotkey)
00ad33e5 test     al, al                                        
00ad33e7 je       0xad33f9                                      
00ad33e9 xor      r9d, r9d                                      
00ad33ec mov      r8b, 1                                        
00ad33ef mov      edx, esi                                      
00ad33f1 mov      rcx, rbx                                      
00ad33f4 call     0xad46e0                                      System.Void PlayerController::ReadySkill(System.Int32,System.Boolean)
00ad33f9 mov      rax, qword ptr [rbx + 0x408]                  
00ad3400 inc      edi                                           
00ad3402 mov      ecx, edi                                      
00ad3404 test     rax, rax                                      
00ad3407 jne      0xad33b3                                      
00ad3409 call     0x580ca0                                      
00ad340e int3                                                   
00ad340f int3                                                   

System.Void PlayerController::ReadySkill(System.Int32,System.Boolean) RVA=0xad46e0
00ad46e0 mov      qword ptr [rsp + 0x10], rbx                   
00ad46e5 mov      qword ptr [rsp + 0x18], rsi                   
00ad46ea push     rdi                                           
00ad46eb sub      rsp, 0x60                                     
00ad46ef cmp      byte ptr [rip + 0x56987da], 0                 
00ad46f6 movzx    esi, r8b                                      
00ad46fa mov      edi, edx                                      
00ad46fc mov      rbx, rcx                                      
00ad46ff jne      0xad472c                                      
00ad4701 lea      rcx, [rip + 0x52e2d40]                        
00ad4708 call     0x5809f0                                      
00ad470d lea      rcx, [rip + 0x528792c]                        
00ad4714 call     0x5809f0                                      
00ad4719 lea      rcx, [rip + 0x52dd938]                        
00ad4720 call     0x5809f0                                      
00ad4725 mov      byte ptr [rip + 0x56987a4], 1                 
00ad472c xor      r8d, r8d                                      
00ad472f mov      edx, edi                                      
00ad4731 mov      rcx, rbx                                      
00ad4734 call     0xac3e20                                      SkillState PlayerController::GetAssignedSkill(System.Int32)
00ad4739 mov      rdi, rax                                      
00ad473c test     rax, rax                                      
00ad473f je       0xad4911                                      
00ad4745 test     sil, sil                                      
00ad4748 je       0xad475c                                      
00ad474a xor      edx, edx                                      
00ad474c mov      rcx, rax                                      
00ad474f call     0x7d5ed0                                      System.Boolean SkillState::get_CanHoldCast()
00ad4754 test     al, al                                        
00ad4756 je       0xad4911                                      
00ad475c xor      edx, edx                                      
00ad475e mov      qword ptr [rsp + 0x70], rbp                   
00ad4763 mov      rcx, rdi                                      
00ad4766 mov      byte ptr [rbx + 0x383], sil                   
00ad476d call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00ad4772 test     rax, rax                                      
00ad4775 je       0xad495f                                      
00ad477b mov      eax, dword ptr [rax + 0xe4]                   
00ad4781 test     eax, eax                                      
00ad4783 je       0xad4930                                      
00ad4789 cmp      eax, 3                                        
00ad478c je       0xad4930                                      
00ad4792 cmp      qword ptr [rbx + 0x438], 0                    
00ad479a jne      0xad47a1                                      
00ad479c xor      bpl, bpl                                      
00ad479f jmp      0xad47bb                                      
00ad47a1 mov      rax, qword ptr [rbx + 0x438]                  
00ad47a8 xor      r8d, r8d                                      
00ad47ab mov      rdx, qword ptr [rdi + 0x10]                   
00ad47af mov      rcx, qword ptr [rax + 0x10]                   
00ad47b3 call     0x2df7870                                     
00ad47b8 movzx    ebp, al                                       
00ad47bb cmp      byte ptr [rbx + 0x381], 0                     
00ad47c2 jne      0xad494f                                      
00ad47c8 xor      sil, 1                                        
00ad47cc test     bpl, sil                                      
00ad47cf jne      0xad4924                                      
00ad47d5 lea      rcx, [rbx + 0x438]                            
00ad47dc mov      qword ptr [rbx + 0x438], rdi                  
00ad47e3 mov      rdx, rdi                                      
00ad47e6 call     0x57fd40                                      
00ad47eb xor      edx, edx                                      
00ad47ed mov      rcx, rbx                                      
00ad47f0 call     0xc22620                                      
00ad47f5 test     rax, rax                                      
00ad47f8 je       0xad495f                                      
00ad47fe xor      edx, edx                                      
00ad4800 mov      rcx, rax                                      
00ad4803 call     0xca75c0                                      
00ad4808 test     al, al                                        
00ad480a je       0xad490c                                      
00ad4810 test     bpl, bpl                                      
00ad4813 jne      0xad490c                                      
00ad4819 mov      rcx, qword ptr [rip + 0x5287820]              
00ad4820 mov      rsi, qword ptr [rbx + 0x428]                  
00ad4827 cmp      dword ptr [rcx + 0xe4], 0                     
00ad482e jne      0xad4835                                      
00ad4830 call     0x580d30                                      
00ad4835 xor      r8d, r8d                                      
00ad4838 xor      edx, edx                                      
00ad483a mov      rcx, rsi                                      
00ad483d call     0x443d9f0                                     
00ad4842 test     al, al                                        
00ad4844 je       0xad48f5                                      
00ad484a mov      rax, qword ptr [rip + 0x52e2bf7]              
00ad4851 cmp      dword ptr [rax + 0xe4], 0                     
00ad4858 jne      0xad4869                                      
00ad485a mov      rcx, rax                                      
00ad485d call     0x580d30                                      
00ad4862 mov      rax, qword ptr [rip + 0x52e2bdf]              
00ad4869 mov      rax, qword ptr [rax + 0xb8]                   
00ad4870 mov      rcx, qword ptr [rax]                          
00ad4873 test     rcx, rcx                                      
00ad4876 je       0xad495f                                      
00ad487c mov      rax, qword ptr [rip + 0x52dd7d5]              
00ad4883 lea      r9, [rsp + 0x50]                              
00ad4888 movss    xmm0, dword ptr [rip + 0x3e3c3b0]             
00ad4890 xor      edx, edx                                      
00ad4892 movss    xmm2, dword ptr [rip + 0x3e3c54a]             
00ad489a mov      rcx, qword ptr [rcx + 0x48]                   
00ad489e mov      qword ptr [rsp + 0x38], rax                   
00ad48a3 lea      rax, [rsp + 0x40]                             
00ad48a8 mov      qword ptr [rsp + 0x50], rdx                   
00ad48ad movsd    xmm1, qword ptr [rsp + 0x50]                  
00ad48b3 mov      dword ptr [rsp + 0x30], 0xffffffff            
00ad48bb movss    dword ptr [rsp + 0x28], xmm0                  
00ad48c1 movsd    qword ptr [rsp + 0x40], xmm1                  
00ad48c7 movsd    qword ptr [rsp + 0x50], xmm1                  
00ad48cd mov      qword ptr [rsp + 0x20], rax                   
00ad48d2 mov      dword ptr [rsp + 0x48], edx                   
00ad48d6 mov      dword ptr [rsp + 0x58], edx                   
00ad48da call     0x10ad2b0                                     T PoolingUtils::Spawn(T,UnityEngine.Transform,System.Single,UnityEngine.Vector3,UnityEngine.Vector3,System.Single,System.Int32)
00ad48df lea      rcx, [rbx + 0x428]                            
00ad48e6 mov      qword ptr [rbx + 0x428], rax                  
00ad48ed mov      rdx, rax                                      
00ad48f0 call     0x57fd40                                      
00ad48f5 mov      rcx, qword ptr [rbx + 0x428]                  
00ad48fc test     rcx, rcx                                      
00ad48ff je       0xad495f                                      
00ad4901 xor      r8d, r8d                                      
00ad4904 mov      rdx, rdi                                      
00ad4907 call     0x89fac0                                      System.Void UIReadySkillIndicator::Draw(SkillState)
00ad490c mov      rbp, qword ptr [rsp + 0x70]                   
00ad4911 mov      rbx, qword ptr [rsp + 0x78]                   
00ad4916 mov      rsi, qword ptr [rsp + 0x80]                   
00ad491e add      rsp, 0x60                                     
00ad4922 pop      rdi                                           
00ad4923 ret                                                    
00ad4924 xor      edx, edx                                      
00ad4926 mov      rcx, rbx                                      
00ad4929 call     0xac1050                                      System.Void PlayerController::ClearSkillReady()
00ad492e jmp      0xad490c                                      
00ad4930 lea      rcx, [rbx + 0x438]                            
00ad4937 mov      qword ptr [rbx + 0x438], rdi                  
00ad493e mov      rdx, rdi                                      
00ad4941 call     0x57fd40                                      
00ad4946 cmp      byte ptr [rbx + 0x381], 0                     
00ad494d je       0xad490c                                      
00ad494f xor      r8d, r8d                                      
00ad4952 mov      rdx, rdi                                      
00ad4955 mov      rcx, rbx                                      
00ad4958 call     0xac3180                                      System.Void PlayerController::FastCast(SkillState)
00ad495d jmp      0xad490c                                      
00ad495f call     0x580ca0                                      
00ad4964 int3                                                   
00ad4965 int3                                                   
00ad4966 int3                                                   
00ad4967 int3                                                   
00ad4968 int3                                                   
00ad4969 int3                                                   
00ad496a int3                                                   
00ad496b int3                                                   
00ad496c int3                                                   
00ad496d int3                                                   
00ad496e int3                                                   
00ad496f int3                                                   
