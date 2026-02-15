// ═══ CONCATENATED SOURCE: nft-stake-vault ═══

// ═══ FILE: lib.rs ═══
use anchor_lang::prelude::*;

mod instructions;
mod state;
mod utils;

use instructions::*;

declare_id!("FZaTXcKpGef7ew74UHpJAkrZAfhMTZbSFJ297aKjURXN");

#[constant]
pub const WEIGHT: u128 = 1_000_000_000;

#[program]
pub mod nft_stake_vault {
    use super::*;

    pub fn init_staking(
        ctx: Context<InitStaking>, 
        reward: u64, 
        minimum_period: i64,
        staking_starts_at: i64,
        staking_ends_at: i64,
        max_stakers_count: u64
    ) -> Result<()> {
        init_staking_handler(ctx, reward, minimum_period, staking_starts_at, staking_ends_at, max_stakers_count)
    }

    pub fn stake(ctx: Context<Stake>) -> Result<()> {
        stake_handler(ctx)
    }

    pub fn withdraw_reward(ctx: Context<WithdrawReward>) -> Result<()> {
        withdraw_reward_handler(ctx)
    }

    pub fn unstake(ctx: Context<Unstake>) -> Result<()> {
        unstake_handler(ctx)
    }

    pub fn extend_staking(ctx: Context<ExtendStaking>, new_end_time: i64) -> Result<()> {
        extend_staking_handler(ctx, new_end_time)
    }

    pub fn change_reward(ctx: Context<ChangeReward>, new_reward: u64) -> Result<()> {
        change_reward_handler(ctx, new_reward)
    }

    pub fn add_funds(ctx: Context<AddFunds>, amount: u64) -> Result<()> {
        add_funds_handler(ctx, amount)
    }

    pub fn close_staking(ctx: Context<CloseStaking>) -> Result<()> {
        close_staking_handler(ctx)
    }
}

#[error_code]
pub enum StakeError {
    #[msg("unable to get stake details bump")]
    StakeBumpError,
    #[msg("unable to get nft record bump")]
    NftBumpError,
    #[msg("the minimum staking period in secs can't be negative")]
    NegativePeriodValue,
    #[msg("stake ends time must be greater than the current time & start time")]
    InvalidStakeEndTime,
    #[msg("the given mint account doesn't belong to NFT")]
    TokenNotNFT,
    #[msg("the given token account has no token")]
    TokenAccountEmpty,
    #[msg("the collection field in the metadata is not verified")]
    CollectionNotVerified,
    #[msg("the collection doesn't match the staking details")]
    InvalidCollection,
    #[msg("max staker count reached")]
    MaxStakersReached,
    #[msg("the minimum stake period for the rewards not completed yet")]
    IneligibleForReward,
    #[msg("the nft stake time is greator than the staking period")]
    StakingIsOver,
    #[msg("the staking is not yet started")]
    StakingNotLive,
    #[msg("the staking is not currently active")]
    StakingInactive,
    #[msg("Insufficient tokens in Vault to extend the period or reward")]
    InsufficientBalInVault,
    #[msg("failed to convert the time to u64")]
    FailedTimeConversion,
    #[msg("failed to convert the weight to u64")]
    FailedWeightConversion,
    #[msg("unable to add the given values")]
    ProgramAddError,
    #[msg("unable to subtract the given values")]
    ProgramSubError,
    #[msg("unable to multiply the given values")]
    ProgramMulError,
    #[msg("unable to divide the given values")]
    ProgramDivError,
}
// ═══ FILE: state/mod.rs ═══
mod stake_details;
mod nft_record;

pub use stake_details::*;
pub use nft_record::*;

// ═══ FILE: state/stake_details.rs ═══
use anchor_lang::prelude::*;

use crate::{StakeError, WEIGHT};

#[account]
pub struct Details {
    /// The status of the staking (1)
    pub is_active: bool,
    /// The creator of the stake record (32)
    pub creator: Pubkey,
    /// The mint of the token to be given as reward (32)
    pub reward_mint: Pubkey,
    /// The record of the current and prev reward emissions
    pub reward: Vec<u64>,
    /// the record of the time when reward emission changed
    pub reward_change_time: Vec<i64>,
    /// The verified collection address of the NFT (32)
    pub collection: Pubkey,
    /// The max number of NFTs that can be staked (8)
    pub max_stakers_count: u64,
    /// The current number of NFTs staked (8)
    pub current_stakers_count: u64,
    /// Accrued weight of the staked NFTs (16)
    pub staked_weight: u128, 
    /// The starting time of the staking (8)
    pub staking_starts_at: i64,
    /// The period for which staking is funded (8)
    pub staking_ends_at: i64,
    /// The minimum stake period to be eligible for reward - in seconds (8)
    pub minimum_period: i64,
    /// The bump of the stake record PDA (1)
    pub stake_bump: u8,
    /// The bump of the token authority PDA (1)
    pub token_auth_bump: u8,
    /// The bump of the nft authority PDA (1)
    pub nft_auth_bump: u8,
    /// The current balance in Stake Vault (8)
    pub current_balance: u64
}

impl Details {
    pub const LEN: usize = 8 + 1 + 32 + 32 + 12 + 12 + 32 + 8 + 8 + 16 + 8 + 8 + 8 + 1 + 1 + 1 + 8;

    pub fn init(
        creator: Pubkey,
        reward_mint: Pubkey,
        collection: Pubkey,
        reward: u64,
        max_stakers_count: u64,
        staking_starts_at: i64,
        staking_ends_at: i64,
        minimum_period: i64,
        stake_bump: u8,
        token_auth_bump: u8,
        nft_auth_bump: u8,
        current_balance: u64
    ) -> Self {
        Self {
            is_active: true,
            creator,
            reward_mint,
            collection,
            reward: vec![reward],
            reward_change_time: vec![staking_starts_at],
            max_stakers_count,
            staked_weight: 0,
            current_stakers_count: 0,
            staking_starts_at,
            staking_ends_at,
            minimum_period,
            stake_bump,
            token_auth_bump,
            nft_auth_bump,
            current_balance
        }
    }

    pub fn current_len(&self) -> usize {
        (Details::LEN - 16) + (self.reward.len() * 16)
    }

    pub fn change_reward(&mut self, new_reward: u64, current_time: i64) {
        self.reward.push(new_reward);
        self.reward_change_time.push(current_time);
    }

    pub fn extend_staking(&mut self, new_end_time: i64) {
        self.staking_ends_at = new_end_time;
    }

    pub fn update_staked_weight(&mut self, stake_time: i64, increase_weight: bool) -> Result<()> {
        let last_reward_time = *self.reward_change_time.last().unwrap();

        let base = self.staking_ends_at
            .checked_sub(last_reward_time)
            .ok_or(StakeError::ProgramSubError)? as u128; // directly converting to u128 since it can't be negative

        let weight_time = stake_time.max(last_reward_time);

        let mut num = self.staking_ends_at
            .checked_sub(weight_time)
            .ok_or(StakeError::ProgramSubError)? as u128; // directly converting to u128 since it can't be negative

        num = num.checked_mul(WEIGHT).ok_or(StakeError::ProgramMulError)?;
        
        let weight = num.checked_div(base).ok_or(StakeError::ProgramDivError)?;

        if increase_weight {
            self.staked_weight = self.staked_weight.checked_add(weight).ok_or(StakeError::ProgramAddError)?;
        } else {
            self.staked_weight = self.staked_weight.checked_sub(weight).ok_or(StakeError::ProgramSubError)?;
        }

        Ok(())
    }

    pub fn increase_staker_count(&mut self) -> Result<()> {
        self.current_stakers_count = self.current_stakers_count
        .checked_add(1)
        .ok_or(StakeError::ProgramAddError)?;
        
        Ok(())
    }

    pub fn decrease_staker_count(&mut self) -> Result<()> {
        self.current_stakers_count = self.current_stakers_count
        .checked_sub(1)
        .ok_or(StakeError::ProgramSubError)?;
        
        Ok(())
    }
    
    pub fn increase_current_balance(&mut self, added_funds: u64) -> Result<()> {
        self.current_balance = self.current_balance
            .checked_add(added_funds)
            .ok_or(StakeError::ProgramAddError)?;
        
        Ok(())
    }

    pub fn decrease_current_balance(&mut self, staked_at: i64, current_time: i64) -> Result<()> {
        let last_reward_time = *self.reward_change_time.last().unwrap();
        let last_reward = *self.reward.last().unwrap();

        let reward_time = staked_at.max(last_reward_time);
        let cutoff_time = current_time.min(self.staking_ends_at);

        let rewardable_time_since_change = cutoff_time
            .checked_sub(reward_time)
            .ok_or(StakeError::ProgramSubError)?;

        let rewardable_time_u64 = match u64::try_from(rewardable_time_since_change) {
            Ok(time) => time,
            _ => return err!(StakeError::FailedTimeConversion)
        };

        let reward_since_change = last_reward
            .checked_mul(rewardable_time_u64)
            .ok_or(StakeError::ProgramMulError)?;

        self.current_balance = self.current_balance
            .checked_sub(reward_since_change)
            .ok_or(StakeError::ProgramSubError)?;
        
        Ok(())
    }

    pub fn close_staking(&mut self) {
        self.is_active = false;
    }
}
// ═══ FILE: state/nft_record.rs ═══
use anchor_lang::prelude::*;

#[account]
pub struct NftRecord {
    /// The owner/staker of the NFT (32)
    pub staker: Pubkey,
    /// The mint of the staked NFT (32)
    pub nft_mint: Pubkey,
    /// The staking timestamp (8)
    pub staked_at: i64,
    /// The bump of NFT Record PDA (1)
    pub bump: u8
}

impl NftRecord {
    pub const LEN: usize = 8 + 32 + 32 + 8 + 1;

    pub fn init(staker: Pubkey, nft_mint: Pubkey, staked_at: i64, bump: u8) -> Self {
        Self {staker, nft_mint, staked_at, bump}
    }
}
// ═══ FILE: utils/mod.rs ═══
pub use calc_reward::*;
pub use calc_total_emission::*;
pub use calc_actual_balance::*;

pub mod calc_reward;
pub mod calc_total_emission;
pub mod calc_actual_balance;

// ═══ FILE: utils/calc_reward.rs ═══
use anchor_lang::prelude::*;
use crate::StakeError;

pub fn calc_reward(
    staked_at: i64,
    minimum_stake_period: i64,
    reward_emission: &Vec<u64>,
    reward_change_time: &Vec<i64>,
    staking_ends_at: i64
) -> Result<(u64, i64, bool)> {
    let clock = Clock::get().unwrap();
    let current_time = clock.unix_timestamp;

    let reward_eligible_time = staked_at.checked_add(minimum_stake_period).ok_or(StakeError::ProgramAddError)?;
    let is_eligible_for_reward = current_time >= reward_eligible_time;

    let cutoff_time = i64::min(current_time, staking_ends_at);
    
    // The index during which NFT staked
    let stake_index = reward_change_time.binary_search(&staked_at);

    let index = match stake_index {
        Ok(i) => i,
        Err(i) => i - 1
    };

    let mut reward_tokens: u64 = 0;
    let total_changes = reward_change_time.len() - 1;

    // Going through every reward change between NFT staked and reward claimed
    for ix in index..=total_changes {
        let big_num = if ix == total_changes { cutoff_time } else { reward_change_time[ix + 1] };
        let sml_num = if ix == index { staked_at } else { reward_change_time[ix] };

        let rewardable_time = big_num.checked_sub(sml_num).ok_or(StakeError::ProgramSubError)?;

        let rewardable_time = match u64::try_from(rewardable_time) {
            Ok(time) => time,
            _ => return err!(StakeError::FailedTimeConversion)
        };

        let reward = rewardable_time.checked_mul(reward_emission[ix]).ok_or(StakeError::ProgramMulError)?;

        reward_tokens = reward_tokens.checked_add(reward).ok_or(StakeError::ProgramAddError)?;
    }

    Ok((reward_tokens, current_time, is_eligible_for_reward))
}

// ═══ FILE: utils/calc_actual_balance.rs ═══
use anchor_lang::prelude::*;
use crate::{StakeError, WEIGHT};

pub fn calc_actual_balance(
    current_stakers_count: u64,
    staked_weight: u128,
    last_reward_rate: u64,
    last_reward_time: i64,
    staking_ends_at: i64,
    current_time: i64,
    current_balance: u64,
    new_end_time: Option<i64>
) -> Result<(u64, u128)> {
    let avg_staked_weight = if staked_weight == 0 {
        staked_weight
    } else {
        staked_weight
        .checked_div(current_stakers_count as u128)
        .ok_or(StakeError::ProgramDivError)? + 1
    };

    // Total time since last reward change to stake end
    let total_time = staking_ends_at
        .checked_sub(last_reward_time)
        .ok_or(StakeError::ProgramSubError)?;

    let total_time_u128 = match u128::try_from(total_time) {
        Ok(time) => time,
        _ => return err!(StakeError::FailedTimeConversion)
    };

    // Time between average staking time and stake end
    let stake_to_end_time_weighted = total_time_u128
        .checked_mul(avg_staked_weight)
        .ok_or(StakeError::ProgramMulError)?;

    let stake_to_end_time = stake_to_end_time_weighted
        .checked_div(WEIGHT)
        .ok_or(StakeError::ProgramDivError)? + 1;

    let stake_to_end_time = match u64::try_from(stake_to_end_time) {
        Ok(time) => time,
        _ => return err!(StakeError::FailedTimeConversion)
    };

    // Calculate Rewardable Time
    let rewardable_time = if staking_ends_at > current_time {
        // If the current time is less than the stake end time,
        // Subtract the unaccrued time from the stake to end time
        let unaccrued_time = staking_ends_at
            .checked_sub(current_time)
            .ok_or(StakeError::ProgramSubError)?;

        let unaccrued_time_u64 = match u64::try_from(unaccrued_time) {
            Ok(time) => time,
            _ => return err!(StakeError::FailedTimeConversion)
        };

        stake_to_end_time
        .checked_sub(unaccrued_time_u64)
        .ok_or(StakeError::ProgramSubError)?
    } else {
        // If the current time is greater or equal to the stake end time,
        // add seconds since the stake end time to the rewardable time
        let accrued_time = current_time
            .checked_sub(staking_ends_at)
            .ok_or(StakeError::ProgramSubError)?;

        let accrued_time_u64 = match u64::try_from(accrued_time) {
            Ok(time) => time,
            _ => return err!(StakeError::FailedTimeConversion)
        };

        stake_to_end_time
        .checked_add(accrued_time_u64)
        .ok_or(StakeError::ProgramAddError)?
    };

    // The rewards yet to be paid (per staker)
    let accrued_reward = last_reward_rate
        .checked_mul(rewardable_time)
        .ok_or(StakeError::ProgramMulError)?;

    // The rewards yet to be paid (all stakers)
    let accrued_reward = accrued_reward
        .checked_mul(current_stakers_count)
        .ok_or(StakeError::ProgramMulError)?;

    // The current actual balance after deducting accrual rewards
    let current_actual_balance = current_balance
        .checked_sub(accrued_reward)
        .ok_or(StakeError::ProgramSubError)?;

    // THE CALCULATION OF THE NEW STAKED WEIGHT
    let new_staked_weight = match new_end_time {
        Some(new_time) => {
            let stake_to_old_end = match i64::try_from(stake_to_end_time) {
                Ok(stake_to_end) => stake_to_end,
                _ => return err!(StakeError::FailedTimeConversion)
            };

            let time_added = new_time
                .checked_sub(staking_ends_at)
                .ok_or(StakeError::ProgramSubError
            )?;

            // Add extended time to stake period
            let stake_to_new_end = stake_to_old_end
                .checked_add(time_added)
                .ok_or(StakeError::ProgramAddError
            )?;

            let new_base = new_time
                .checked_sub(last_reward_time)
                .ok_or(StakeError::ProgramSubError
            )?;

            let stake_to_new_end_u128 = match u128::try_from(stake_to_new_end) {
                Ok(stake_to_end) => stake_to_end,
                _ => return err!(StakeError::FailedTimeConversion)
            };

            let new_base_u128 = match u128::try_from(new_base) {
                Ok(base) => base,
                _ => return err!(StakeError::FailedTimeConversion)
            };

            let new_num = stake_to_new_end_u128.checked_mul(WEIGHT).ok_or(StakeError::ProgramMulError)?;

            // New average staked weight
            let new_weight = new_num.checked_div(new_base_u128).ok_or(StakeError::ProgramDivError)?;

            // New total staked weight
            new_weight.checked_mul(current_stakers_count as u128).ok_or(StakeError::ProgramMulError)?
        },
        None => {
            // Return the whole weight if reward is changed
            WEIGHT.checked_mul(current_stakers_count as u128).ok_or(StakeError::ProgramMulError)?
        }
    };

    Ok((current_actual_balance, new_staked_weight))
}
// ═══ FILE: utils/calc_total_emission.rs ═══
use anchor_lang::prelude::*;
use crate::StakeError;

pub fn calc_total_emission(
    reward: u64,
    max_stakers_count: u64,
    staking_starts_at: i64,
    staking_ends_at: i64
) -> Result<u64> {
    let total_staking_period = staking_ends_at.checked_sub(staking_starts_at).ok_or(StakeError::ProgramSubError)?;

    let rewardable_time_u64 = match u64::try_from(total_staking_period) {
        Ok(time) => time,
        _ => return err!(StakeError::FailedTimeConversion)
    };

    let total_rewardable_time = rewardable_time_u64.checked_mul(max_stakers_count).ok_or(StakeError::ProgramMulError)?;
    let total_emission = total_rewardable_time.checked_mul(reward).ok_or(StakeError::ProgramMulError)?;

    Ok(total_emission)
}

// ═══ FILE: instructions/mod.rs ═══
pub use init_staking::*;
pub use stake::*;
pub use withdraw_reward::*;
pub use unstake::*;
pub use extend_staking::*;
pub use change_reward::*;
pub use add_funds::*;
pub use close_staking::*;

pub mod init_staking;
pub mod stake;
pub mod withdraw_reward;
pub mod unstake;
pub mod extend_staking;
pub mod change_reward;
pub mod add_funds;
pub mod close_staking;
// ═══ FILE: instructions/init_staking.rs ═══
use anchor_lang::prelude::*;
use anchor_spl::{
    token::{Mint, Token, TokenAccount, Transfer, transfer}, 
    associated_token::AssociatedToken
};

use crate::{state::Details, StakeError, utils::calc_total_emission};

#[derive(Accounts)]
pub struct InitStaking<'info> {
    #[account(
        init, 
        payer = creator, 
        space = Details::LEN,
        seeds = [
            b"stake", 
            collection_address.key().as_ref(),
            creator.key().as_ref()
        ],
        bump
    )]
    pub stake_details: Account<'info, Details>,

    pub token_mint: Account<'info, Mint>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = creator
    )]
    pub token_account: Account<'info, TokenAccount>,

    #[account(
        init_if_needed,
        payer = creator,
        associated_token::mint = token_mint,
        associated_token::authority = token_authority,
    )]
    pub stake_token_vault: Account<'info, TokenAccount>,

    #[account(
        mint::decimals = 0,
    )]
    pub collection_address: Account<'info, Mint>,

    #[account(mut)]
    pub creator: Signer<'info>,

    /// CHECK: This account is not read or written
    #[account(
        seeds = [
            b"token-authority",
            stake_details.key().as_ref()
        ],
        bump
    )]
    pub token_authority: UncheckedAccount<'info>,

    /// CHECK: This account is not read or written
    #[account(
        seeds = [
            b"nft-authority",
            stake_details.key().as_ref()
        ],
        bump
    )]
    pub nft_authority: UncheckedAccount<'info>,

    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>
}

impl<'info> InitStaking<'info> {
    pub fn transfer_token_ctx(&self) -> CpiContext<'_, '_, '_, 'info, Transfer<'info>> {
        let cpi_accounts = Transfer {
            from: self.token_account.to_account_info(),
            to: self.stake_token_vault.to_account_info(),
            authority: self.creator.to_account_info()
        };
    
        let cpi_program = self.token_program.to_account_info();

        CpiContext::new(cpi_program, cpi_accounts)
    }
}

pub fn init_staking_handler(
    ctx: Context<InitStaking>, 
    reward: u64, 
    minimum_period: i64,
    staking_starts_at: i64,
    staking_ends_at: i64,
    max_stakers_count: u64
) -> Result<()> {
    let clock = Clock::get().unwrap();
    let current_time = clock.unix_timestamp;

    require_gte!(minimum_period, 0, StakeError::NegativePeriodValue);
    require_gt!(staking_ends_at, current_time, StakeError::InvalidStakeEndTime);
    require_gt!(staking_ends_at, staking_starts_at, StakeError::InvalidStakeEndTime);

    let reward_mint = ctx.accounts.token_mint.key();
    let collection = ctx.accounts.collection_address.key();
    let creator = ctx.accounts.creator.key();
    let stake_bump = *ctx.bumps.get("stake_details").ok_or(StakeError::StakeBumpError)?;
    let token_auth_bump = *ctx.bumps.get("token_authority").ok_or(StakeError::StakeBumpError)?;
    let nft_auth_bump = *ctx.bumps.get("nft_authority").ok_or(StakeError::StakeBumpError)?;

    let total_emission = calc_total_emission(reward, max_stakers_count, staking_starts_at, staking_ends_at)?;

    transfer(ctx.accounts.transfer_token_ctx(), total_emission)?;

    let stake_details = &mut ctx.accounts.stake_details;

    **stake_details = Details::init(
        creator,
        reward_mint, 
        collection,
        reward,
        max_stakers_count,
        staking_starts_at,
        staking_ends_at,
        minimum_period,
        stake_bump,
        token_auth_bump,
        nft_auth_bump,
        total_emission
    );


    Ok(())
}
// ═══ FILE: instructions/stake.rs ═══
use anchor_lang::prelude::*;
use anchor_spl::{
    token::{Mint, Token, transfer, TokenAccount, Transfer}, 
    metadata::{MasterEditionAccount, MetadataAccount, Metadata}, 
    associated_token::AssociatedToken
};

use crate::{state::{Details, NftRecord}, StakeError};

#[derive(Accounts)]
pub struct Stake<'info> {
    #[account(
        mut,
        seeds = [
            b"stake", 
            stake_details.collection.as_ref(),
            stake_details.creator.as_ref()
        ],
        bump = stake_details.stake_bump
    )]
    pub stake_details: Account<'info, Details>,

    #[account(
        init,
        payer = signer,
        space = NftRecord::LEN,
        seeds = [
            b"nft-record", 
            stake_details.key().as_ref(),
            nft_mint.key().as_ref(),
        ],
        bump
    )]
    pub nft_record: Account<'info, NftRecord>,

    #[account(
        mint::decimals = 0,
        constraint = nft_mint.supply == 1 @ StakeError::TokenNotNFT
    )]
    nft_mint: Account<'info, Mint>,

    #[account(
        mut,
        associated_token::mint = nft_mint,
        associated_token::authority = signer,
        constraint = nft_token.amount == 1 @ StakeError::TokenAccountEmpty
    )]
    nft_token: Account<'info, TokenAccount>,

    #[account(
        seeds = [
            b"metadata",
            Metadata::id().as_ref(),
            nft_mint.key().as_ref()
        ],
        seeds::program = Metadata::id(),
        bump,
        constraint = nft_metadata.collection.as_ref().unwrap().verified @ StakeError::CollectionNotVerified,
        constraint = nft_metadata.collection.as_ref().unwrap().key == stake_details.collection @ StakeError::InvalidCollection
    )]
    nft_metadata: Box<Account<'info, MetadataAccount>>,

    #[account(
        seeds = [
            b"metadata",
            Metadata::id().as_ref(),
            nft_mint.key().as_ref(),
            b"edition"
        ],
        seeds::program = Metadata::id(),
        bump
    )]
    nft_edition: Box<Account<'info, MasterEditionAccount>>,

    /// CHECK: This account is not read or written
    #[account(
        seeds = [
            b"nft-authority",
            stake_details.key().as_ref()
        ],
        bump = stake_details.nft_auth_bump
    )]
    pub nft_authority: UncheckedAccount<'info>,

    #[account(
        init_if_needed,
        payer = signer,
        associated_token::mint = nft_mint,
        associated_token::authority = nft_authority
    )]
    pub nft_custody: Account<'info, TokenAccount>,

    #[account(mut)]
    pub signer: Signer<'info>,

    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>
}

impl<'info> Stake<'info> {
    pub fn transfer_nft_ctx(&self) -> CpiContext<'_, '_, '_, 'info, Transfer<'info>> {
        let cpi_accounts = Transfer {
            from: self.nft_token.to_account_info(),
            to: self.nft_custody.to_account_info(),
            authority: self.signer.to_account_info()
        };
    
        let cpi_program = self.token_program.clone().to_account_info();

        CpiContext::new(cpi_program, cpi_accounts)
    }
}

pub fn stake_handler(ctx: Context<Stake>) -> Result<()> {
    let stake_details = &ctx.accounts.stake_details;

    let Details { 
        current_stakers_count: current_stakers,
        max_stakers_count: max_stakers,
        staking_starts_at,
        staking_ends_at,
        is_active: staking_status,
        ..
    } = **stake_details;

    let current_time = Clock::get().unwrap().unix_timestamp;
    
    require_eq!(staking_status, true, StakeError::StakingInactive);
    require_gt!(max_stakers, current_stakers, StakeError::MaxStakersReached);
    require_gte!(current_time, staking_starts_at, StakeError::StakingNotLive);
    require_gte!(staking_ends_at, current_time, StakeError::StakingIsOver);

    let staker = ctx.accounts.signer.key();
    let nft_mint = ctx.accounts.nft_mint.key();
    let bump = *ctx.bumps.get("nft_record").ok_or(StakeError::NftBumpError)?;

    transfer(ctx.accounts.transfer_nft_ctx(), 1)?;

    let nft_record = &mut ctx.accounts.nft_record;
    **nft_record = NftRecord::init(staker, nft_mint, current_time, bump);

    let stake_details = &mut ctx.accounts.stake_details;

    // Add stake weight and increase staker count
    stake_details.update_staked_weight(current_time, true)?;
    stake_details.increase_staker_count()
}
// ═══ FILE: instructions/withdraw_reward.rs ═══
use anchor_lang::prelude::*;
use anchor_spl::{
    token::{Mint, Token, TokenAccount, Transfer, transfer}, 
    associated_token::AssociatedToken
};

use crate::{state::{Details, NftRecord}, utils::calc_reward, StakeError};

#[derive(Accounts)]
pub struct WithdrawReward<'info> {
    #[account(
        mut,
        seeds = [
            b"stake", 
            stake_details.collection.as_ref(),
            stake_details.creator.as_ref()
        ],
        bump = stake_details.stake_bump,
        has_one = reward_mint
    )]
    pub stake_details: Account<'info, Details>,

    #[account(
        mut,
        seeds = [
            b"nft-record", 
            stake_details.key().as_ref(),
            nft_record.nft_mint.as_ref(),
        ],
        bump = nft_record.bump,
        has_one = staker
    )]
    pub nft_record: Account<'info, NftRecord>,

    pub reward_mint: Account<'info, Mint>,

    #[account(
        mut,
        associated_token::mint = reward_mint,
        associated_token::authority = token_authority
    )]
    pub stake_token_vault: Account<'info, TokenAccount>,

    #[account(
        init_if_needed,
        payer = staker,
        associated_token::mint = reward_mint,
        associated_token::authority = staker
    )]
    pub reward_receive_account: Account<'info, TokenAccount>,

    /// CHECK: This account is not read or written
    #[account(
        seeds = [
            b"token-authority",
            stake_details.key().as_ref(),
        ],
        bump = stake_details.token_auth_bump
    )]
    pub token_authority: UncheckedAccount<'info>,

    #[account(mut)]
    pub staker: Signer<'info>,

    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>
}

impl<'info> WithdrawReward<'info> {
    pub fn transfer_token_ctx(&self) -> CpiContext<'_, '_, '_, 'info, Transfer<'info>> {
        let cpi_accounts = Transfer {
            from: self.stake_token_vault.to_account_info(),
            to: self.reward_receive_account.to_account_info(),
            authority: self.token_authority.to_account_info()
        };
    
        let cpi_program = self.token_program.to_account_info();

        CpiContext::new(cpi_program, cpi_accounts)
    }
}

pub fn withdraw_reward_handler(ctx: Context<WithdrawReward>) -> Result<()> {
    let stake_details = &ctx.accounts.stake_details;

    let Details {
        minimum_period,
        staking_ends_at,
        is_active: staking_status,
        token_auth_bump,
        ..
    } = **stake_details;

    let reward_record = &stake_details.reward;
    let reward_change_time_record = &stake_details.reward_change_time;
    let stake_details_key = stake_details.key();

    let staked_at = ctx.accounts.nft_record.staked_at;
    
    require_eq!(staking_status, true, StakeError::StakingInactive);
    require_gte!(staking_ends_at, staked_at, StakeError::StakingIsOver);

    let (reward_tokens, current_time, is_eligible_for_reward) = calc_reward(
        staked_at, 
        minimum_period, 
        reward_record,
        reward_change_time_record,
        staking_ends_at
    ).unwrap();

    if is_eligible_for_reward {
        let authority_seed = &[&b"token-authority"[..], &stake_details_key.as_ref(), &[token_auth_bump]];

        transfer(
            ctx.accounts.transfer_token_ctx().with_signer(&[&authority_seed[..]]), 
            reward_tokens)?;
    } else {
        return err!(StakeError::IneligibleForReward);
    }

    ctx.accounts.nft_record.staked_at = current_time;

    let stake_details = &mut ctx.accounts.stake_details;

    // Remove previous stake weight
    stake_details.update_staked_weight(staked_at, false)?;

    // Add new stake weight
    stake_details.update_staked_weight(current_time, true)?;

    // Decrease the balance in record
    stake_details.decrease_current_balance(staked_at, current_time)
 
}
// ═══ FILE: instructions/unstake.rs ═══
use anchor_lang::prelude::*;
use anchor_spl::{
    token::{Mint, Token, TokenAccount, Transfer, CloseAccount, transfer, close_account}, 
    associated_token::AssociatedToken
};

use crate::{state::{Details, NftRecord}, utils::calc_reward, StakeError};

#[derive(Accounts)]
pub struct Unstake<'info> {
    #[account(
        mut,
        seeds = [
            b"stake", 
            stake_details.collection.as_ref(),
            stake_details.creator.as_ref()
        ],
        bump = stake_details.stake_bump,
        has_one = reward_mint
    )]
    pub stake_details: Account<'info, Details>,

    #[account(
        mut,
        seeds = [
            b"nft-record", 
            stake_details.key().as_ref(),
            nft_record.nft_mint.as_ref(),
        ],
        bump = nft_record.bump,
        has_one = nft_mint,
        has_one = staker,
        close = staker
    )]
    pub nft_record: Account<'info, NftRecord>,

    pub reward_mint: Account<'info, Mint>,

    #[account(
        mut,
        associated_token::mint = reward_mint,
        associated_token::authority = token_authority
    )]
    pub stake_token_vault: Account<'info, TokenAccount>,

    #[account(
        init_if_needed,
        payer = staker,
        associated_token::mint = reward_mint,
        associated_token::authority = staker
    )]
    pub reward_receive_account: Box<Account<'info, TokenAccount>>,

    #[account(
        mint::decimals = 0,
        constraint = nft_mint.supply == 1 @ StakeError::TokenNotNFT,
    )]
    nft_mint: Box<Account<'info, Mint>>,

    #[account(
        init_if_needed,
        payer = staker,
        associated_token::mint = nft_mint,
        associated_token::authority = staker,
    )]
    nft_receive_account: Box<Account<'info, TokenAccount>>,

    #[account(
        mut,
        associated_token::mint = nft_mint,
        associated_token::authority = nft_authority,
        constraint = nft_custody.amount == 1 @ StakeError::TokenAccountEmpty,
        close = staker
    )]
    pub nft_custody: Box<Account<'info, TokenAccount>>,

    /// CHECK: This account is not read or written
    #[account(
        seeds = [
            b"token-authority",
            stake_details.key().as_ref(),
        ],
        bump = stake_details.token_auth_bump
    )]
    pub token_authority: UncheckedAccount<'info>,

     /// CHECK: This account is not read or written
     #[account(
        seeds = [
            b"nft-authority",
            stake_details.key().as_ref()
        ],
        bump = stake_details.nft_auth_bump
    )]
    pub nft_authority: UncheckedAccount<'info>,

    #[account(mut)]
    pub staker: Signer<'info>,

    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>
}

impl<'info> Unstake<'info> {
    pub fn transfer_token_ctx(&self) -> CpiContext<'_, '_, '_, 'info, Transfer<'info>> {
        let cpi_accounts = Transfer {
            from: self.stake_token_vault.to_account_info(),
            to: self.reward_receive_account.to_account_info(),
            authority: self.token_authority.to_account_info()
        };
    
        let cpi_program = self.token_program.to_account_info();

        CpiContext::new(cpi_program, cpi_accounts)
    }

    pub fn transfer_nft_ctx(&self) -> CpiContext<'_, '_, '_, 'info, Transfer<'info>> {
        let cpi_accounts = Transfer {
            from: self.nft_custody.to_account_info(),
            to: self.nft_receive_account.to_account_info(),
            authority: self.nft_authority.to_account_info()
        };
    
        let cpi_program = self.token_program.clone().to_account_info();

        CpiContext::new(cpi_program, cpi_accounts)
    }

    pub fn close_account_ctx(&self)-> CpiContext<'_, '_, '_, 'info, CloseAccount<'info>> {
        let cpi_accounts = CloseAccount {
            account: self.nft_custody.to_account_info(),
            destination: self.staker.to_account_info(),
            authority: self.nft_authority.to_account_info()
        };
        let cpi_program = self.token_program.to_account_info();
        CpiContext::new(cpi_program, cpi_accounts)
    }
}

pub fn unstake_handler(ctx: Context<Unstake>) -> Result<()> {
    let stake_details = &ctx.accounts.stake_details;

    let Details {
        minimum_period,
        staking_ends_at,
        token_auth_bump,
        nft_auth_bump,
        ..
    } = **stake_details;

    let reward_record = &stake_details.reward;
    let reward_change_time_record = &stake_details.reward_change_time;
    let stake_details_key = stake_details.key();

    let staked_at = ctx.accounts.nft_record.staked_at;
    
    let (reward_tokens, current_time, is_eligible_for_reward) = calc_reward(
        staked_at, 
        minimum_period, 
        reward_record,
        reward_change_time_record,
        staking_ends_at
    ).unwrap();

    if is_eligible_for_reward {
        // Transfer Reward Tokens
        let token_auth_seed = &[&b"token-authority"[..], &stake_details_key.as_ref(), &[token_auth_bump]];
        transfer(
            ctx.accounts.transfer_token_ctx().with_signer(&[&token_auth_seed[..]]), 
            reward_tokens
        )?;
    }

    // Transfer NFT
    let nft_auth_seed = &[&b"nft-authority"[..], &stake_details_key.as_ref(), &[nft_auth_bump]];
    transfer(
        ctx.accounts.transfer_nft_ctx().with_signer(&[&nft_auth_seed[..]]), 
        1
    )?;

    // Close NFT Custody Account
    close_account(ctx.accounts.close_account_ctx().with_signer(&[&nft_auth_seed[..]]))?;
    
    let stake_details = &mut ctx.accounts.stake_details;

    // Delete stake weight and reduce staker count
    stake_details.update_staked_weight(staked_at, false)?; 
    stake_details.decrease_staker_count()?;

    // Decrease the balance in record
    stake_details.decrease_current_balance(staked_at, current_time)
}
// ═══ FILE: instructions/extend_staking.rs ═══
use anchor_lang::prelude::*;

use crate::{state::Details, utils::{calc_total_emission, calc_actual_balance}, StakeError};

#[derive(Accounts)]
pub struct ExtendStaking<'info> {
    #[account(
        mut,
        seeds = [
            b"stake", 
            stake_details.collection.as_ref(),
            stake_details.creator.as_ref()
        ],
        bump = stake_details.stake_bump,
        has_one = creator
    )]
    pub stake_details: Account<'info, Details>,

    pub creator: Signer<'info>,
}

pub fn extend_staking_handler(ctx: Context<ExtendStaking>, new_ending_time: i64) -> Result<()> {
    let stake_details = &ctx.accounts.stake_details;
    let current_time = Clock::get().unwrap().unix_timestamp;

    let Details {
        max_stakers_count,
        current_stakers_count,
        staking_ends_at,
        current_balance,
        staked_weight,
        is_active: staking_status,
        ..
    } = **stake_details;

    let current_reward = *stake_details.reward.last().unwrap();
    let last_reward_change_time = *stake_details.reward_change_time.last().unwrap();

    require_eq!(staking_status, true, StakeError::StakingInactive);
    require_gt!(new_ending_time, current_time, StakeError::InvalidStakeEndTime);
    require_gt!(new_ending_time, staking_ends_at, StakeError::InvalidStakeEndTime);
    
    let (current_actual_balance, new_staked_weight) = calc_actual_balance(
        current_stakers_count,
        staked_weight,
        current_reward,
        last_reward_change_time,
        staking_ends_at,
        current_time,
        current_balance,
        Some(new_ending_time)
    )?;

    let new_emission = calc_total_emission(
        current_reward, 
        max_stakers_count, 
        current_time, 
        new_ending_time
    )?;

    require_gte!(current_actual_balance, new_emission, StakeError::InsufficientBalInVault);

    let stake_details = &mut ctx.accounts.stake_details;

    stake_details.extend_staking(new_ending_time);
    stake_details.staked_weight = new_staked_weight;

    Ok(())
}
// ═══ FILE: instructions/change_reward.rs ═══
use anchor_lang::prelude::*;

use crate::{state::Details, utils::{calc_total_emission, calc_actual_balance}, StakeError};

#[derive(Accounts)]
pub struct ChangeReward<'info> {
    #[account(
        mut,
        seeds = [
            b"stake", 
            stake_details.collection.as_ref(),
            stake_details.creator.as_ref()
        ],
        bump = stake_details.stake_bump,
        has_one = creator,
        realloc = stake_details.current_len() + 16,
        realloc::payer = creator,
        realloc::zero = false
    )]
    pub stake_details: Account<'info, Details>,

    #[account(mut)]
    pub creator: Signer<'info>,

    pub system_program: Program<'info, System>
}

pub fn change_reward_handler(ctx: Context<ChangeReward>, new_reward: u64) -> Result<()> {
    let stake_details = &ctx.accounts.stake_details;
    let current_time = Clock::get().unwrap().unix_timestamp;

    let Details {
        max_stakers_count,
        current_stakers_count,
        staking_ends_at,
        current_balance,
        staked_weight,
        is_active: staking_status,
        ..
    } = **stake_details;

    let current_reward = *stake_details.reward.last().unwrap();
    let last_reward_change_time = *stake_details.reward_change_time.last().unwrap();

    require_gte!(staking_ends_at, current_time, StakeError::StakingIsOver);
    require_eq!(staking_status, true, StakeError::StakingInactive);

    let (current_actual_balance, new_staked_weight) = calc_actual_balance(
        current_stakers_count,
        staked_weight,
        current_reward,
        last_reward_change_time,
        staking_ends_at,
        current_time,
        current_balance,
        None
    )?;

    let new_emission = calc_total_emission(
        new_reward, 
        max_stakers_count, 
        current_time, 
        staking_ends_at
    )?;

    require_gte!(current_actual_balance, new_emission, StakeError::InsufficientBalInVault);

    let stake_details = &mut ctx.accounts.stake_details;

    stake_details.change_reward(new_reward, current_time);
    stake_details.current_balance = current_actual_balance;
    stake_details.staked_weight = new_staked_weight;

    Ok(())
}
// ═══ FILE: instructions/add_funds.rs ═══
use anchor_lang::prelude::*;
use anchor_spl::token::{transfer, Transfer, Token, TokenAccount, Mint};

use crate::{state::Details, StakeError};

#[derive(Accounts)]
pub struct AddFunds<'info> {
    #[account(
        mut,
        seeds = [
            b"stake", 
            stake_details.collection.as_ref(),
            stake_details.creator.as_ref()
        ],
        bump = stake_details.stake_bump,
        has_one = creator,
        has_one = reward_mint
    )]
    pub stake_details: Account<'info, Details>,

    pub reward_mint: Account<'info, Mint>,

    #[account(
        mut,
        associated_token::mint = reward_mint,
        associated_token::authority = creator
    )]
    pub token_account: Account<'info, TokenAccount>,

    #[account(
        mut,
        associated_token::mint = reward_mint,
        associated_token::authority = token_authority,
    )]
    pub stake_token_vault: Account<'info, TokenAccount>,

    /// CHECK: This account is not read or written
    #[account(
        seeds = [
            b"token-authority",
            stake_details.key().as_ref()
        ],
        bump = stake_details.token_auth_bump
    )]
    pub token_authority: UncheckedAccount<'info>,

    pub creator: Signer<'info>,
    pub token_program: Program<'info, Token>
}

impl<'info> AddFunds<'info> {
    pub fn transfer_token_ctx(&self) -> CpiContext<'_, '_, '_, 'info, Transfer<'info>> {
        let cpi_accounts = Transfer {
            from: self.token_account.to_account_info(),
            to: self.stake_token_vault.to_account_info(),
            authority: self.creator.to_account_info()
        };
    
        let cpi_program = self.token_program.to_account_info();

        CpiContext::new(cpi_program, cpi_accounts)
    }
}

pub fn add_funds_handler(ctx: Context<AddFunds>, amount: u64) -> Result<()> {
    let stake_status = ctx.accounts.stake_details.is_active;

    require_eq!(stake_status, true, StakeError::StakingInactive);

    transfer(ctx.accounts.transfer_token_ctx(), amount)?;
    ctx.accounts.stake_details.increase_current_balance(amount)
}
// ═══ FILE: instructions/close_staking.rs ═══
use anchor_lang::prelude::*;
use anchor_spl::token::{transfer, Transfer, Token, TokenAccount, Mint};

use crate::{state::Details, StakeError, utils::calc_actual_balance};

#[derive(Accounts)]
pub struct CloseStaking<'info> {
    #[account(
        mut,
        seeds = [
            b"stake", 
            stake_details.collection.as_ref(),
            stake_details.creator.as_ref()
        ],
        bump = stake_details.stake_bump,
        has_one = creator
    )]
    pub stake_details: Account<'info, Details>,

    pub token_mint: Account<'info, Mint>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = creator
    )]
    pub token_account: Account<'info, TokenAccount>,

    #[account(
        mut,
        associated_token::mint = token_mint,
        associated_token::authority = token_authority,
    )]
    pub stake_token_vault: Account<'info, TokenAccount>,

    /// CHECK: This account is not read or written
    #[account(
        seeds = [
            b"token-authority",
            stake_details.key().as_ref()
        ],
        bump
    )]
    pub token_authority: UncheckedAccount<'info>,

    pub creator: Signer<'info>,
    pub token_program: Program<'info, Token>
}

impl<'info> CloseStaking<'info> {
    pub fn transfer_token_ctx(&self) -> CpiContext<'_, '_, '_, 'info, Transfer<'info>> {
        let cpi_accounts = Transfer {
            from: self.stake_token_vault.to_account_info(),
            to: self.token_account.to_account_info(),
            authority: self.token_authority.to_account_info()
        };
    
        let cpi_program = self.token_program.to_account_info();

        CpiContext::new(cpi_program, cpi_accounts)
    }
}

pub fn close_staking_handler(ctx: Context<CloseStaking>) -> Result<()> {
    let stake_details = &ctx.accounts.stake_details;
    let current_time = Clock::get().unwrap().unix_timestamp;

    let Details {
        current_stakers_count,
        staking_ends_at,
        staked_weight,
        is_active: staking_status,
        token_auth_bump,
        ..
    } = **stake_details;

    let current_reward = *stake_details.reward.last().unwrap();
    let last_reward_change_time = *stake_details.reward_change_time.last().unwrap();
    let stake_details_key = stake_details.key();

    let current_balance = ctx.accounts.stake_token_vault.amount;
    
    require_eq!(staking_status, true, StakeError::StakingInactive);

    let (current_actual_balance, _new_staked_weight) = calc_actual_balance(
        current_stakers_count,
        staked_weight,
        current_reward,
        last_reward_change_time,
        staking_ends_at,
        current_time,
        current_balance,
        None
    )?;

    // Transfer remaining balance back to the creator
    let token_auth_seed = &[&b"token-authority"[..], &stake_details_key.as_ref(), &[token_auth_bump]];
    transfer(
        ctx.accounts.transfer_token_ctx().with_signer(&[&token_auth_seed[..]]), 
        current_actual_balance
    )?;

    let stake_details = &mut ctx.accounts.stake_details;

    stake_details.close_staking();

    // Allow stakers to instantly withdraw their NFTs
    stake_details.minimum_period = 0;

    // If the staking end time is more than the current time then change it to current
    // This is done to avoid accrual of any new stake rewards
    stake_details.staking_ends_at = if staking_ends_at > current_time {
        current_time
    } else {
        staking_ends_at
    };

    Ok(())
}