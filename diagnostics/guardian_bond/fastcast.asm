
System.Boolean SkillsComponent::IsValidCastTarget(BaseUnitController,SkillState) RVA=0x7bdef0
007bdef0 mov      qword ptr [rsp + 8], rbx                      
007bdef5 mov      qword ptr [rsp + 0x10], rsi                   
007bdefa push     rdi                                           
007bdefb sub      rsp, 0x20                                     
007bdeff cmp      byte ptr [rip + 0x59adb15], 0                 
007bdf06 mov      rdi, r8                                       
007bdf09 mov      rbx, rdx                                      
007bdf0c mov      rsi, rcx                                      
007bdf0f jne      0x7bdf24                                      
007bdf11 lea      rcx, [rip + 0x559e128]                        
007bdf18 call     0x5809f0                                      
007bdf1d mov      byte ptr [rip + 0x59adaf7], 1                 
007bdf24 test     rdi, rdi                                      
007bdf27 je       0x7be031                                      
007bdf2d xor      edx, edx                                      
007bdf2f mov      rcx, rdi                                      
007bdf32 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
007bdf37 test     rax, rax                                      
007bdf3a je       0x7be031                                      
007bdf40 cmp      dword ptr [rax + 0xe4], 1                     
007bdf47 jne      0x7be01f                                      
007bdf4d mov      rcx, qword ptr [rip + 0x559e0ec]              
007bdf54 cmp      dword ptr [rcx + 0xe4], 0                     
007bdf5b jne      0x7bdf62                                      
007bdf5d call     0x580d30                                      
007bdf62 xor      r8d, r8d                                      
007bdf65 xor      edx, edx                                      
007bdf67 mov      rcx, rbx                                      
007bdf6a call     0x443d9f0                                     
007bdf6f test     al, al                                        
007bdf71 jne      0x7be00d                                      
007bdf77 test     rbx, rbx                                      
007bdf7a je       0x7be031                                      
007bdf80 mov      rdx, qword ptr [rsi + 0x30]                   
007bdf84 xor      r8d, r8d                                      
007bdf87 mov      rcx, qword ptr [rbx + 0x30]                   
007bdf8b call     0xaafa20                                      System.Boolean MapConditionUtility::IsVisible(FishNet.Object.NetworkObject,FishNet.Object.NetworkObject)
007bdf90 test     al, al                                        
007bdf92 je       0x7be00d                                      
007bdf94 xor      edx, edx                                      
007bdf96 mov      rcx, rbx                                      
007bdf99 call     0x6efee0                                      System.Boolean BaseUnitController::get_IsInvulnerable()
007bdf9e test     al, al                                        
007bdfa0 je       0x7bdfd0                                      
007bdfa2 mov      rcx, qword ptr [rip + 0x559e097]              
007bdfa9 mov      rsi, qword ptr [rsi + 0x128]                  
007bdfb0 cmp      dword ptr [rcx + 0xe4], 0                     
007bdfb7 jne      0x7bdfbe                                      
007bdfb9 call     0x580d30                                      
007bdfbe xor      r8d, r8d                                      
007bdfc1 mov      rdx, rsi                                      
007bdfc4 mov      rcx, rbx                                      
007bdfc7 call     0x443db80                                     
007bdfcc test     al, al                                        
007bdfce jne      0x7be00d                                      
007bdfd0 mov      rcx, qword ptr [rbx + 0x128]                  
007bdfd7 test     rcx, rcx                                      
007bdfda je       0x7be031                                      
007bdfdc xor      edx, edx                                      
007bdfde call     0xaa7380                                      System.Boolean HealthComponent::get_IsAlive()
007bdfe3 test     al, al                                        
007bdfe5 jne      0x7be01f                                      
007bdfe7 xor      edx, edx                                      
007bdfe9 mov      rcx, rdi                                      
007bdfec call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
007bdff1 test     rax, rax                                      
007bdff4 je       0x7be031                                      
007bdff6 mov      rcx, qword ptr [rax + 0x208]                  
007bdffd test     rcx, rcx                                      
007be000 je       0x7be031                                      
007be002 xor      edx, edx                                      
007be004 call     0x7d3700                                      System.Boolean ScaledValue::HasValue()
007be009 test     al, al                                        
007be00b jne      0x7be01f                                      
007be00d xor      al, al                                        
007be00f mov      rbx, qword ptr [rsp + 0x30]                   
007be014 mov      rsi, qword ptr [rsp + 0x38]                   
007be019 add      rsp, 0x20                                     
007be01d pop      rdi                                           
007be01e ret                                                    
007be01f mov      rbx, qword ptr [rsp + 0x30]                   
007be024 mov      al, 1                                         
007be026 mov      rsi, qword ptr [rsp + 0x38]                   
007be02b add      rsp, 0x20                                     
007be02f pop      rdi                                           
007be030 ret                                                    
007be031 call     0x580ca0                                      
007be036 int3                                                   
007be037 int3                                                   
007be038 int3                                                   
007be039 int3                                                   
007be03a int3                                                   
007be03b int3                                                   
007be03c int3                                                   
007be03d int3                                                   
007be03e int3                                                   
007be03f int3                                                   

System.Boolean PlayerController::CanTargetAsAlly(BaseUnitController) RVA=0xabca10
00abca10 push     rbx                                           
00abca12 sub      rsp, 0x20                                     
00abca16 cmp      byte ptr [rip + 0x56b048d], 0                 
00abca1d mov      rbx, rcx                                      
00abca20 jne      0xabca41                                      
00abca22 lea      rcx, [rip + 0x52faa1f]                        
00abca29 call     0x5809f0                                      
00abca2e lea      rcx, [rip + 0x529f60b]                        
00abca35 call     0x5809f0                                      
00abca3a mov      byte ptr [rip + 0x56b0469], 1                 
00abca41 mov      rcx, qword ptr [rip + 0x529f5f8]              
00abca48 cmp      dword ptr [rcx + 0xe4], 0                     
00abca4f jne      0xabca56                                      
00abca51 call     0x580d30                                      
00abca56 xor      edx, edx                                      
00abca58 mov      rcx, rbx                                      
00abca5b call     0x443daf0                                     
00abca60 test     al, al                                        
00abca62 je       0xabcb0a                                      
00abca68 test     rbx, rbx                                      
00abca6b je       0xabcb12                                      
00abca71 mov      rcx, qword ptr [rbx + 0x148]                  
00abca78 test     rcx, rcx                                      
00abca7b je       0xabcb12                                      
00abca81 xor      edx, edx                                      
00abca83 call     0x819f50                                      BaseUnitController SummoningComponent::get_Summoner()
00abca88 mov      rcx, qword ptr [rip + 0x529f5b1]              
00abca8f mov      rbx, rax                                      
00abca92 cmp      dword ptr [rcx + 0xe4], 0                     
00abca99 jne      0xabcaa0                                      
00abca9b call     0x580d30                                      
00abcaa0 xor      r8d, r8d                                      
00abcaa3 xor      edx, edx                                      
00abcaa5 mov      rcx, rbx                                      
00abcaa8 call     0x443d9f0                                     
00abcaad test     al, al                                        
00abcaaf je       0xabcab9                                      
00abcab1 mov      al, 1                                         
00abcab3 add      rsp, 0x20                                     
00abcab7 pop      rbx                                           
00abcab8 ret                                                    
00abcab9 mov      rcx, qword ptr [rip + 0x52fa988]              
00abcac0 mov      qword ptr [rsp + 0x30], rdi                   
00abcac5 cmp      dword ptr [rcx + 0xe4], 0                     
00abcacc jne      0xabcad3                                      
00abcace call     0x580d30                                      
00abcad3 xor      ecx, ecx                                      
00abcad5 call     0x6e1ce0                                      PlayerController App::get_Player()
00abcada mov      rcx, qword ptr [rip + 0x529f55f]              
00abcae1 mov      rdi, rax                                      
00abcae4 cmp      dword ptr [rcx + 0xe4], 0                     
00abcaeb jne      0xabcaf2                                      
00abcaed call     0x580d30                                      
00abcaf2 xor      r8d, r8d                                      
00abcaf5 mov      rdx, rdi                                      
00abcaf8 mov      rcx, rbx                                      
00abcafb mov      rdi, qword ptr [rsp + 0x30]                   
00abcb00 add      rsp, 0x20                                     
00abcb04 pop      rbx                                           
00abcb05 jmp      0x443d9f0                                     
00abcb0a xor      al, al                                        
00abcb0c add      rsp, 0x20                                     
00abcb10 pop      rbx                                           
00abcb11 ret                                                    
00abcb12 call     0x580ca0                                      
00abcb17 int3                                                   
00abcb18 int3                                                   
00abcb19 int3                                                   
00abcb1a int3                                                   
00abcb1b int3                                                   
00abcb1c int3                                                   
00abcb1d int3                                                   
00abcb1e int3                                                   
00abcb1f int3                                                   

System.Void PlayerController::FastCast(SkillState) RVA=0xac3180
00ac3180 mov      qword ptr [rsp + 0x18], rbx                   
00ac3185 push     rdi                                           
00ac3186 sub      rsp, 0x40                                     
00ac318a cmp      byte ptr [rip + 0x56a9d40], 0                 
00ac3191 mov      rdi, rdx                                      
00ac3194 mov      rbx, rcx                                      
00ac3197 jne      0xac31dc                                      
00ac3199 lea      rcx, [rip + 0x52f42a8]                        
00ac31a0 call     0x5809f0                                      
00ac31a5 lea      rcx, [rip + 0x52b71ec]                        
00ac31ac call     0x5809f0                                      
00ac31b1 lea      rcx, [rip + 0x52b44f8]                        
00ac31b8 call     0x5809f0                                      
00ac31bd lea      rcx, [rip + 0x52f3cdc]                        
00ac31c4 call     0x5809f0                                      
00ac31c9 lea      rcx, [rip + 0x5298e70]                        
00ac31d0 call     0x5809f0                                      
00ac31d5 mov      byte ptr [rip + 0x56a9cf5], 1                 
00ac31dc mov      qword ptr [rsp + 0x58], 0                     
00ac31e5 test     rdi, rdi                                      
00ac31e8 je       0xac34b8                                      
00ac31ee mov      rcx, qword ptr [rip + 0x52f4253]              
00ac31f5 cmp      dword ptr [rcx + 0xe4], 0                     
00ac31fc jne      0xac3203                                      
00ac31fe call     0x580d30                                      
00ac3203 xor      ecx, ecx                                      
00ac3205 call     0x652230                                      System.Boolean App::get_IsServer()
00ac320a test     al, al                                        
00ac320c je       0xac3227                                      
00ac320e xor      r8d, r8d                                      
00ac3211 mov      rdx, rdi                                      
00ac3214 mov      rcx, rbx                                      
00ac3217 call     0xad2da0                                      System.Void PlayerController::ProcessFastCast(SkillState)
00ac321c mov      rbx, qword ptr [rsp + 0x60]                   
00ac3221 add      rsp, 0x40                                     
00ac3225 pop      rdi                                           
00ac3226 ret                                                    
00ac3227 xor      edx, edx                                      
00ac3229 mov      qword ptr [rsp + 0x50], rsi                   
00ac322e mov      rcx, rdi                                      
00ac3231 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00ac3236 test     rax, rax                                      
00ac3239 je       0xac34c3                                      
00ac323f mov      eax, dword ptr [rax + 0xe4]                   
00ac3245 cmp      eax, 1                                        
00ac3248 jne      0xac3434                                      
00ac324e mov      rcx, qword ptr [rip + 0x5298deb]              
00ac3255 mov      rsi, qword ptr [rbx + 0x2e8]                  
00ac325c cmp      dword ptr [rcx + 0xe4], 0                     
00ac3263 jne      0xac326a                                      
00ac3265 call     0x580d30                                      
00ac326a xor      r8d, r8d                                      
00ac326d xor      edx, edx                                      
00ac326f mov      rcx, rsi                                      
00ac3272 call     0x443d9f0                                     
00ac3277 test     al, al                                        
00ac3279 je       0xac32e1                                      
00ac327b mov      rcx, qword ptr [rip + 0x5298dbe]              
00ac3282 mov      rsi, qword ptr [rbx + 0x2e0]                  
00ac3289 cmp      dword ptr [rcx + 0xe4], 0                     
00ac3290 jne      0xac3297                                      
00ac3292 call     0x580d30                                      
00ac3297 xor      r8d, r8d                                      
00ac329a xor      edx, edx                                      
00ac329c mov      rcx, rsi                                      
00ac329f call     0x443d9f0                                     
00ac32a4 test     al, al                                        
00ac32a6 je       0xac32e1                                      
00ac32a8 xor      edx, edx                                      
00ac32aa mov      rcx, rdi                                      
00ac32ad call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00ac32b2 test     rax, rax                                      
00ac32b5 je       0xac34c3                                      
00ac32bb mov      eax, dword ptr [rax + 0xe0]                   
00ac32c1 cmp      eax, 3                                        
00ac32c4 je       0xac32cb                                      
00ac32c6 cmp      eax, 1                                        
00ac32c9 jne      0xac32e1                                      
00ac32cb lea      rcx, [rbx + 0x2e8]                            
00ac32d2 mov      qword ptr [rbx + 0x2e8], rbx                  
00ac32d9 mov      rdx, rbx                                      
00ac32dc call     0x57fd40                                      
00ac32e1 mov      rcx, qword ptr [rip + 0x5298d58]              
00ac32e8 mov      rsi, qword ptr [rbx + 0x2e0]                  
00ac32ef cmp      dword ptr [rcx + 0xe4], 0                     
00ac32f6 jne      0xac32fd                                      
00ac32f8 call     0x580d30                                      
00ac32fd xor      edx, edx                                      
00ac32ff mov      rcx, rsi                                      
00ac3302 call     0x443daf0                                     
00ac3307 test     al, al                                        
00ac3309 je       0xac333a                                      
00ac330b mov      rcx, qword ptr [rbx + 0x138]                  
00ac3312 test     rcx, rcx                                      
00ac3315 je       0xac34c3                                      
00ac331b mov      r8, qword ptr [rbx + 0x2e0]                   
00ac3322 xor      r9d, r9d                                      
00ac3325 mov      rdx, rdi                                      
00ac3328 call     0x7b89e0                                      System.Boolean SkillsComponent::CanHit(SkillState,BaseUnitController)
00ac332d test     al, al                                        
00ac332f je       0xac333a                                      
00ac3331 mov      rcx, qword ptr [rbx + 0x2e0]                  
00ac3338 jmp      0xac3391                                      
00ac333a mov      rcx, qword ptr [rip + 0x5298cff]              
00ac3341 mov      rsi, qword ptr [rbx + 0x2e8]                  
00ac3348 cmp      dword ptr [rcx + 0xe4], 0                     
00ac334f jne      0xac3356                                      
00ac3351 call     0x580d30                                      
00ac3356 xor      edx, edx                                      
00ac3358 mov      rcx, rsi                                      
00ac335b call     0x443daf0                                     
00ac3360 test     al, al                                        
00ac3362 je       0xac33ac                                      
00ac3364 mov      rcx, qword ptr [rbx + 0x138]                  
00ac336b test     rcx, rcx                                      
00ac336e je       0xac34c3                                      
00ac3374 mov      r8, qword ptr [rbx + 0x2e8]                   
00ac337b xor      r9d, r9d                                      
00ac337e mov      rdx, rdi                                      
00ac3381 call     0x7b89e0                                      System.Boolean SkillsComponent::CanHit(SkillState,BaseUnitController)
00ac3386 test     al, al                                        
00ac3388 je       0xac33ac                                      
00ac338a mov      rcx, qword ptr [rbx + 0x2e8]                  
00ac3391 test     rcx, rcx                                      
00ac3394 je       0xac34c3                                      
00ac339a xor      edx, edx                                      
00ac339c call     0xc22560                                      
00ac33a1 mov      dword ptr [rbx + 0x36c], eax                  
00ac33a7 jmp      0xac34a5                                      
00ac33ac xor      edx, edx                                      
00ac33ae mov      rcx, rdi                                      
00ac33b1 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00ac33b6 test     rax, rax                                      
00ac33b9 je       0xac34c3                                      
00ac33bf cmp      byte ptr [rax + 0x69], 0                      
00ac33c3 jne      0xac342d                                      
00ac33c5 cmp      qword ptr [rbx + 0x2f0], 0                    
00ac33cd je       0xac34b3                                      
00ac33d3 mov      r8, qword ptr [rbx + 0x2f0]                   
00ac33da mov      ecx, 2                                        
00ac33df mov      rdx, qword ptr [rip + 0x52f3aba]              
00ac33e6 call     0x30d0                                        
00ac33eb test     rax, rax                                      
00ac33ee je       0xac34c3                                      
00ac33f4 mov      r8, qword ptr [rip + 0x52b42b5]               
00ac33fb lea      rdx, [rsp + 0x58]                             
00ac3400 mov      rcx, rax                                      
00ac3403 call     0xfb2ea0                                      
00ac3408 test     al, al                                        
00ac340a je       0xac34b3                                      
00ac3410 mov      rcx, qword ptr [rsp + 0x58]                   
00ac3415 test     rcx, rcx                                      
00ac3418 je       0xac34c3                                      
00ac341e xor      edx, edx                                      
00ac3420 call     0xc22560                                      
00ac3425 mov      dword ptr [rbx + 0x370], eax                  
00ac342b jmp      0xac34a5                                      
00ac342d lea      rcx, [rsp + 0x20]                             
00ac3432 jmp      0xac343e                                      
00ac3434 cmp      eax, 2                                        
00ac3437 jne      0xac34a5                                      
00ac3439 lea      rcx, [rsp + 0x30]                             
00ac343e xor      r9d, r9d                                      
00ac3441 mov      r8, rdi                                       
00ac3444 mov      rdx, rbx                                      
00ac3447 call     0xad7b50                                      UnityEngine.Vector3 PlayerController::ResolveGroundCastPosition(SkillState)
00ac344c mov      rcx, qword ptr [rip + 0x52b6f45]              
00ac3453 movsd    xmm0, qword ptr [rax]                         
00ac3457 cmp      dword ptr [rcx + 0xe4], 0                     
00ac345e mov      esi, dword ptr [rax + 8]                      
00ac3461 movsd    qword ptr [rsp + 0x68], xmm0                  
00ac3467 jne      0xac3474                                      
00ac3469 call     0x580d30                                      
00ac346e movsd    xmm0, qword ptr [rsp + 0x68]                  
00ac3474 xor      r8d, r8d                                      
00ac3477 movsd    qword ptr [rsp + 0x20], xmm0                  
00ac347d lea      rdx, [rsp + 0x20]                             
00ac3482 mov      dword ptr [rsp + 0x28], esi                   
00ac3486 lea      rcx, [rsp + 0x30]                             
00ac348b call     0x7f8040                                      UnityEngine.Vector3Int Extensions::CompressV3(UnityEngine.Vector3)
00ac3490 movsd    xmm0, qword ptr [rax]                         
00ac3494 mov      ecx, dword ptr [rax + 8]                      
00ac3497 movsd    qword ptr [rbx + 0x340], xmm0                 
00ac349f mov      dword ptr [rbx + 0x348], ecx                  
00ac34a5 xor      r8d, r8d                                      
00ac34a8 mov      rdx, rdi                                      
00ac34ab mov      rcx, rbx                                      
00ac34ae call     0xad2da0                                      System.Void PlayerController::ProcessFastCast(SkillState)
00ac34b3 mov      rsi, qword ptr [rsp + 0x50]                   
00ac34b8 mov      rbx, qword ptr [rsp + 0x60]                   
00ac34bd add      rsp, 0x40                                     
00ac34c1 pop      rdi                                           
00ac34c2 ret                                                    
00ac34c3 call     0x580ca0                                      
00ac34c8 int3                                                   
00ac34c9 int3                                                   
00ac34ca int3                                                   
00ac34cb int3                                                   
00ac34cc int3                                                   
00ac34cd int3                                                   
00ac34ce int3                                                   
00ac34cf int3                                                   

System.Void PlayerController::ProcessFastCast(SkillState) RVA=0xad2da0
00ad2da0 mov      qword ptr [rsp + 0x10], rbx                   
00ad2da5 push     rdi                                           
00ad2da6 sub      rsp, 0x40                                     
00ad2daa cmp      byte ptr [rip + 0x569a121], 0                 
00ad2db1 mov      rdi, rdx                                      
00ad2db4 mov      rbx, rcx                                      
00ad2db7 jne      0xad2de4                                      
00ad2db9 lea      rcx, [rip + 0x526c650]                        
00ad2dc0 call     0x5809f0                                      
00ad2dc5 lea      rcx, [rip + 0x526c784]                        
00ad2dcc call     0x5809f0                                      
00ad2dd1 lea      rcx, [rip + 0x52a75c0]                        
00ad2dd8 call     0x5809f0                                      
00ad2ddd mov      byte ptr [rip + 0x569a0ee], 1                 
00ad2de4 xor      r8d, r8d                                      
00ad2de7 mov      rdx, rdi                                      
00ad2dea mov      rcx, rbx                                      
00ad2ded call     0xac0670                                      System.Void PlayerController::CheckCast_C(SkillState)
00ad2df2 lea      rcx, [rbx + 0x438]                            
00ad2df9 mov      qword ptr [rbx + 0x438], rdi                  
00ad2e00 mov      rdx, rdi                                      
00ad2e03 call     0x57fd40                                      
00ad2e08 test     rdi, rdi                                      
00ad2e0b je       0xad2f84                                      
00ad2e11 xor      edx, edx                                      
00ad2e13 mov      rcx, rdi                                      
00ad2e16 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00ad2e1b test     rax, rax                                      
00ad2e1e je       0xad2f84                                      
00ad2e24 mov      eax, dword ptr [rax + 0xe4]                   
00ad2e2a test     eax, eax                                      
00ad2e2c je       0xad2f70                                      
00ad2e32 sub      eax, 1                                        
00ad2e35 je       0xad2e45                                      
00ad2e37 sub      eax, 1                                        
00ad2e3a je       0xad2e5f                                      
00ad2e3c cmp      eax, 1                                        
00ad2e3f je       0xad2f70                                      
00ad2e45 cmp      dword ptr [rbx + 0x36c], 0                    
00ad2e4c jg       0xad2f39                                      
00ad2e52 cmp      dword ptr [rbx + 0x370], 0                    
00ad2e59 jg       0xad2f00                                      
00ad2e5f movsd    xmm0, qword ptr [rbx + 0x340]                 
00ad2e67 xor      edx, edx                                      
00ad2e69 movsd    qword ptr [rsp + 0x20], xmm0                  
00ad2e6f cmp      dword ptr [rsp + 0x20], edx                   
00ad2e73 jne      0xad2e9b                                      
00ad2e75 mov      rax, qword ptr [rsp + 0x20]                   
00ad2e7a mov      ecx, edx                                      
00ad2e7c shr      rcx, 0x20                                     
00ad2e80 shr      rax, 0x20                                     
00ad2e84 cmp      eax, ecx                                      
00ad2e86 jne      0xad2e9b                                      
00ad2e88 xor      eax, eax                                      
00ad2e8a cmp      dword ptr [rbx + 0x348], edx                  
00ad2e90 sete     al                                            
00ad2e93 test     eax, eax                                      
00ad2e95 jne      0xad2f70                                      
00ad2e9b mov      rcx, qword ptr [rip + 0x52a74f6]              
00ad2ea2 mov      edi, dword ptr [rbx + 0x348]                  
00ad2ea8 cmp      dword ptr [rcx + 0xe4], edx                   
00ad2eae movsd    qword ptr [rsp + 0x50], xmm0                  
00ad2eb4 jne      0xad2ec1                                      
00ad2eb6 call     0x580d30                                      
00ad2ebb movsd    xmm0, qword ptr [rsp + 0x50]                  
00ad2ec1 xor      r8d, r8d                                      
00ad2ec4 movsd    qword ptr [rsp + 0x20], xmm0                  
00ad2eca lea      rdx, [rsp + 0x20]                             
00ad2ecf mov      dword ptr [rsp + 0x28], edi                   
00ad2ed3 lea      rcx, [rsp + 0x30]                             
00ad2ed8 call     0x7f8220                                      UnityEngine.Vector3 Extensions::DecompressV3(UnityEngine.Vector3Int)
00ad2edd xor      r8d, r8d                                      
00ad2ee0 lea      rdx, [rsp + 0x20]                             
00ad2ee5 mov      rcx, rbx                                      
00ad2ee8 movsd    xmm0, qword ptr [rax]                         
00ad2eec mov      eax, dword ptr [rax + 8]                      
00ad2eef movsd    qword ptr [rsp + 0x20], xmm0                  
00ad2ef5 mov      dword ptr [rsp + 0x28], eax                   
00ad2ef9 call     0xad24f0                                      System.Void PlayerController::ProcessClickedPosition(UnityEngine.Vector3)
00ad2efe jmp      0xad2f70                                      
00ad2f00 mov      rcx, qword ptr [rip + 0x52a7491]              
00ad2f07 mov      edi, dword ptr [rbx + 0x370]                  
00ad2f0d cmp      dword ptr [rcx + 0xe4], 0                     
00ad2f14 jne      0xad2f1b                                      
00ad2f16 call     0x580d30                                      
00ad2f1b mov      rdx, qword ptr [rip + 0x526c62e]              
00ad2f22 mov      ecx, edi                                      
00ad2f24 call     0xf8f430                                      T Extensions::GetObjectById(System.Int32)
00ad2f29 xor      r8d, r8d                                      
00ad2f2c mov      rdx, rax                                      
00ad2f2f mov      rcx, rbx                                      
00ad2f32 call     0xad2450                                      System.Void PlayerController::ProcessClickedInteractable(IInteractable)
00ad2f37 jmp      0xad2f70                                      
00ad2f39 mov      rcx, qword ptr [rip + 0x52a7458]              
00ad2f40 mov      edi, dword ptr [rbx + 0x36c]                  
00ad2f46 cmp      dword ptr [rcx + 0xe4], 0                     
00ad2f4d jne      0xad2f54                                      
00ad2f4f call     0x580d30                                      
00ad2f54 mov      rdx, qword ptr [rip + 0x526c4b5]              
00ad2f5b mov      ecx, edi                                      
00ad2f5d call     0xf8f430                                      T Extensions::GetObjectById(System.Int32)
00ad2f62 xor      r8d, r8d                                      
00ad2f65 mov      rdx, rax                                      
00ad2f68 mov      rcx, rbx                                      
00ad2f6b call     0xad2a30                                      System.Boolean PlayerController::ProcessClickedUnit(BaseUnitController)
00ad2f70 xor      edx, edx                                      
00ad2f72 mov      rcx, rbx                                      
00ad2f75 mov      rbx, qword ptr [rsp + 0x58]                   
00ad2f7a add      rsp, 0x40                                     
00ad2f7e pop      rdi                                           
00ad2f7f jmp      0xad3410                                      System.Void PlayerController::ProcessTargeting()
00ad2f84 call     0x580ca0                                      
00ad2f89 int3                                                   
00ad2f8a int3                                                   
00ad2f8b int3                                                   
00ad2f8c int3                                                   
00ad2f8d int3                                                   
00ad2f8e int3                                                   
00ad2f8f int3                                                   
